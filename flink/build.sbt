ThisBuild / scalaVersion := "2.12.18"
ThisBuild / organization := "com.eorzea"

lazy val eorzeaIngestion = (project in file("."))
  .settings(
    name := "Eorzea Ingestion",
    libraryDependencies ++= Seq(
        "org.apache.flink"  % "flink-streaming-java"   % "1.18.0" % "provided",
        "org.apache.flink"  % "flink-connector-kafka"    % "3.1.0-1.18",
        "org.apache.flink"  % "flink-clients"            % "1.18.0" % "provided",
        "org.apache.hudi"   % "hudi-flink1.18-bundle"    % "0.15.0",
        )
  )