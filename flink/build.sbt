ThisBuild / scalaVersion := "2.12.18"
ThisBuild / organization := "com.eorzea"

lazy val eorzeaIngestion = (project in file("."))
  .settings(
    name := "Eorzea Ingestion",
    libraryDependencies ++= Seq(
        "org.apache.flink"  % "flink-streaming-java"   % "1.18.0" % "provided",
        "org.apache.flink"  % "flink-connector-kafka"    % "3.1.0-1.18",
        "org.apache.flink"  % "flink-clients"            % "1.18.0" % "provided",
        "org.apache.flink"  % "flink-table-api-java-bridge" % "1.18.0" % "provided",
        "org.apache.hudi"   % "hudi-flink1.18-bundle"    % "0.15.0",
        "com.fasterxml.jackson.module" %% "jackson-module-scala" % "2.15.3",
        "org.apache.avro"   % "avro"                     % "1.11.1",
    ),
      assembly / assemblyMergeStrategy := {
          case PathList("org", "apache", "hudi", _*) => MergeStrategy.first
          case PathList("META-INF", _*) => MergeStrategy.discard
          case _ => MergeStrategy.first
      }
  )