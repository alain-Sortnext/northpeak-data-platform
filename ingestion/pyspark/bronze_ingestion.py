"""
NorthPeak Retail Group - Bronze Layer Ingestion
Phase 3: Medallion Pipeline Engineering

PySpark extraction from NP Core PostgreSQL -> Bronze Parquet layer.
Maps to: Databricks Runtime on Azure / AWS EMR in enterprise.

Enterprise equivalents:
  - spark.read.jdbc -> Databricks Auto Loader / ADF Copy Activity
  - write.parquet  -> Delta Lake write on ADLS Gen2
  - partitionBy    -> Same in Databricks, adds file compaction

Usage:
  spark-submit bronze_ingestion.py --table orders --date 2026-07-14
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    current_timestamp, lit, to_date, col, when, sha2, trim, upper
)
from pyspark.sql.types import StringType
import logging
import sys
import os
from datetime import date

# ── Logging setup ─────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)
log = logging.getLogger("northpeak.bronze")

# ── Configuration ─────────────────────────────────────────────────
JDBC_URL = os.getenv("NP_CORE_JDBC_URL", "jdbc:postgresql://localhost:5432/np_core")
JDBC_PROPS = {
    "user":     os.getenv("NP_CORE_DB_USER", "pipeline_reader"),
    "password": os.getenv("NP_CORE_DB_PASS", "changeme"),
    "driver":   "org.postgresql.Driver"
}
BRONZE_BASE = os.getenv("BRONZE_PATH", "/tmp/northpeak/bronze")
INGESTION_DATE = os.getenv("INGESTION_DATE", date.today().isoformat())


def create_spark_session():
    """
    Create SparkSession for local mode.
    Enterprise: SparkSession already provided by Databricks cluster.
    """
    return (
        SparkSession.builder
        .appName("NorthPeak-Bronze-Ingestion")
        .master("local[*]")
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
        .config("spark.driver.memory", "2g")
        .getOrCreate()
    )


def extract_table(spark, table_name, schema="np_core"):
    """
    Extract a full table from NP Core PostgreSQL.

    Enterprise equivalent:
      Databricks: spark.read.format('delta').load('abfss://bronze@adls...')
      Auto Loader: spark.readStream.format('cloudFiles')...

    Idempotency: Bronze is append-only, partitioned by ingestion_date.
    Re-running on same date appends duplicate partition (overwrite mode handles this).
    """
    log.info(f"Extracting table: {schema}.{table_name}")
    try:
        df = (
            spark.read
            .jdbc(
                url=JDBC_URL,
                table=f"{schema}.{table_name}",
                properties=JDBC_PROPS
            )
        )
        row_count = df.count()
        log.info(f"Extracted {row_count:,} rows from {table_name}")
        return df, row_count
    except Exception as e:
        log.error(f"Extraction failed for {table_name}: {e}")
        raise


def add_bronze_metadata(df, table_name):
    """
    Add standard Bronze metadata columns to every raw extract.
    These columns are NEVER modified in Bronze - they are audit fields.
    """
    return (
        df
        .withColumn("_bronze_ingested_at", current_timestamp())
        .withColumn("_bronze_source_table", lit(table_name))
        .withColumn("_bronze_source_system", lit("np_core"))
        .withColumn("_bronze_ingestion_date", lit(INGESTION_DATE))
        .withColumn("_bronze_pipeline_version", lit("1.0.0"))
    )


def write_bronze(df, table_name):
    """
    Write DataFrame to Bronze layer as Parquet.

    Partitioned by ingestion_date for efficient downstream reads.
    Overwrite partition to ensure idempotency on reruns.

    Enterprise:
      Replace .parquet() with .format('delta').save() on ADLS Gen2
      Add .option('mergeSchema', 'true') for schema evolution
    """
    output_path = f"{BRONZE_BASE}/np_core/{table_name}"
    log.info(f"Writing Bronze: {output_path} (partition: {INGESTION_DATE})")

    (
        df.write
        .mode("overwrite")
        .partitionBy("_bronze_ingestion_date")
        .parquet(output_path)
    )
    log.info(f"Bronze write complete: {table_name}")


def run_bronze_ingestion(table_name):
    """
    Full Bronze ingestion for one table.
    Build -> Test (row count) -> Submit proof (partition written).
    """
    spark = create_spark_session()
    log.info(f"=== Starting Bronze ingestion: {table_name} | {INGESTION_DATE} ===")

    try:
        # EXTRACT
        df, source_count = extract_table(spark, table_name)

        # ADD METADATA (no transformation - Bronze is raw)
        df_bronze = add_bronze_metadata(df, table_name)

        # VALIDATE row count before write
        if source_count == 0:
            log.warning(f"Zero rows extracted from {table_name} - skipping write")
            return {"status": "skipped", "rows": 0}

        # WRITE
        write_bronze(df_bronze, table_name)

        # VERIFY (read back and count)
        verify_df = spark.read.parquet(f"{BRONZE_BASE}/np_core/{table_name}")
        verify_count = verify_df.filter(
            col("_bronze_ingestion_date") == INGESTION_DATE
        ).count()
        log.info(f"Verification: {verify_count:,} rows written for {INGESTION_DATE}")

        if verify_count != source_count:
            log.error(f"Row count mismatch: source={source_count}, bronze={verify_count}")
            raise RuntimeError("Row count mismatch after Bronze write")

        log.info(f"=== Bronze ingestion COMPLETE: {table_name} | {source_count:,} rows ===")
        return {"status": "success", "table": table_name, "rows": source_count}

    except Exception as e:
        log.error(f"Bronze ingestion FAILED: {table_name} | {e}")
        raise
    finally:
        spark.stop()


if __name__ == "__main__":
    tables = ["orders", "order_items", "customers", "products",
              "stores", "inventory", "stock_movements", "suppliers"]
    table = sys.argv[1] if len(sys.argv) > 1 else "orders"
    if table not in tables:
        print(f"Unknown table: {table}. Valid: {tables}")
        sys.exit(1)
    result = run_bronze_ingestion(table)
    print(result)
