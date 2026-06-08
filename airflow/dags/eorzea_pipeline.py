"""
Eorzea Market Analytics Pipeline DAG

Orchestrates the data pipeline:
1. Ensures the Flink ingestion job is running (submits if not)
2. Runs dbt to refresh mart tables
3. Runs dbt tests for data quality
"""

from datetime import datetime, timedelta
from pathlib import Path
import glob
import json
import time
import urllib.parse
import urllib.request
import urllib.error

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.exceptions import AirflowException


FLINK_API = "http://jobmanager:8081"
FLINK_JAR_DIR = "/opt/airflow/flink-jars"
FLINK_MAIN_CLASS = "com.eorzea.MarketIngestion"


def _flink_api(path, method="GET", data=None):
    """Helper to call the Flink REST API."""
    url = f"{FLINK_API}{path}"
    if data is not None:
        req = urllib.request.Request(url, data=data, method=method)
    else:
        req = urllib.request.Request(url, method=method)
    response = urllib.request.urlopen(req, timeout=15)
    return json.loads(response.read().decode("utf-8"))


def submit_flink_job():
    """Check if the Flink ingestion job is running. If not, upload the jar and submit it."""

    # Check for running jobs
    try:
        jobs_response = _flink_api("/jobs")
        running = [j for j in jobs_response.get("jobs", []) if j["status"] == "RUNNING"]
        if running:
            print(f"Flink job already running: {running[0]['id']}")
            return
    except urllib.error.URLError as e:
        raise AirflowException(f"Cannot reach Flink JobManager: {e}")

    print("No running Flink jobs — submitting ingestion job")

    # Find the fat jar
    jars = glob.glob(f"{FLINK_JAR_DIR}/*.jar")
    if not jars:
        raise AirflowException(f"No jar files found in {FLINK_JAR_DIR}")
    jar_path = jars[0]
    print(f"Using jar: {jar_path}")

    # Upload the jar to Flink
    with open(jar_path, "rb") as f:
        jar_bytes = f.read()

    boundary = "----AirflowBoundary"
    filename = Path(jar_path).name
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="jarfile"; filename="{filename}"\r\n'
        f"Content-Type: application/java-archive\r\n\r\n"
    ).encode() + jar_bytes + f"\r\n--{boundary}--\r\n".encode()

    req = urllib.request.Request(
        f"{FLINK_API}/jars/upload",
        data=body,
        method="POST",
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    upload_response = json.loads(urllib.request.urlopen(req, timeout=60).read().decode("utf-8"))
    jar_id = upload_response["filename"].split("/")[-1]
    print(f"Uploaded jar: {jar_id}")

    # Submit the job
    submit_data = json.dumps({
        "entryClass": FLINK_MAIN_CLASS,
        "parallelism": 1,
    }).encode()
    req = urllib.request.Request(
        f"{FLINK_API}/jars/{urllib.parse.quote(jar_id, safe='')}/run",
        data=submit_data,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    run_response = json.loads(urllib.request.urlopen(req, timeout=30).read().decode("utf-8"))
    job_id = run_response.get("jobid")
    print(f"Submitted Flink job: {job_id}")

    # Verify job started successfully
    time.sleep(5)
    jobs_response = _flink_api("/jobs")
    running = [j for j in jobs_response.get("jobs", []) if j["status"] == "RUNNING"]
    if not running:
        raise AirflowException("Flink job was submitted but is not running — check Flink logs")
    print("Flink job confirmed running")


default_args = {
    "owner": "eorzea",
    "retries": 2,
    "retry_delay": timedelta(minutes=2),
}

with DAG(
    dag_id="eorzea_market_pipeline",
    default_args=default_args,
    description="Full Eorzea market pipeline: ingest, transform, test",
    schedule_interval=timedelta(hours=1),
    start_date=datetime(2026, 5, 27),
    catchup=False,
    tags=["eorzea", "dbt", "flink", "market-data"],
) as dag:

    # Ensure the Flink ingestion job is running
    # Uploads and submits the fat jar via Flink REST API if needed
    submit_flink = PythonOperator(
        task_id="submit_flink_job",
        python_callable=submit_flink_job,
    )

    # Seed static data
    dbt_seed = BashOperator(
        task_id="dbt_seed",
        bash_command=(
            "cd /opt/airflow/dbt && "
            "dbt seed --profiles-dir /opt/airflow/dbt --project-dir /opt/airflow/dbt --target docker"
        ),
    )

    # Refresh dbt models
    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command=(
            "cd /opt/airflow/dbt && "
            "dbt run --profiles-dir /opt/airflow/dbt --project-dir /opt/airflow/dbt --target docker"
        ),
    )

    # DQ checks
    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command=(
            "cd /opt/airflow/dbt && "
            "dbt test --profiles-dir /opt/airflow/dbt --project-dir /opt/airflow/dbt --target docker"
        ),
    )

    submit_flink >> dbt_seed >> dbt_run >> dbt_test
