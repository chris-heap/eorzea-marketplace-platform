ThisBuild / scalaVersion := "2.12.18"
ThisBuild / organization := "com.eorzea"

val flinkVersion = "1.16.3"
val hudiVersion = "0.13.1"

lazy val eorzeaIngestion = (project in file("."))
  .settings(
    name := "Eorzea Ingestion",
    libraryDependencies ++= Seq(
        "org.apache.flink" %% "flink-streaming-scala"       % flinkVersion % "provided",
        "org.apache.flink"  % "flink-clients"                % flinkVersion % "provided",
        "org.apache.flink"  % "flink-connector-kafka"        % "1.16.3",
        "org.apache.flink"  % "flink-table-api-scala-bridge_2.12" % flinkVersion,
        "org.apache.hudi"   % "hudi-flink1.16-bundle"        % hudiVersion,
        "com.fasterxml.jackson.module" %% "jackson-module-scala" % "2.15.3",
        "org.apache.hadoop"  % "hadoop-mapreduce-client-core" % "3.3.6",
    ),
    assembly / assemblyMergeStrategy := {
        case PathList("org", "apache", "hudi", _*) => MergeStrategy.first
        case PathList("META-INF", _*) => MergeStrategy.discard
        case _ => MergeStrategy.first
    }
  )
