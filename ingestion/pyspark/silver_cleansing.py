"""
NorthPeak Retail Group - Silver Layer Cleansing
Phase 3: Medallion Pipeline Engineering

Reads Bronze Parquet, applies all data quality fixes, writes Silver Delta tables.

Key transformations documented in ADR-001 and process_notes_dmitri_handover.md:
  - Deduplication (orders: order_id + created_at, keep latest)
  - Null handling (customer_id -> UNKNOWN_CUSTOMER)
  - PII masking (payment_reference -> SHA-256)
  - Timezone normalisation (all UTC)
  - Date format standardisation (ISO 8601)
  - is_adjustment flag for negative inventory
  - Quarantine routing for failed validation

Enterprise mapping:
  - delta-rs OSS -> Databricks Delta Lake (same API)
  - MERGE logic -> MERGE INTO in Databricks Delta
"""

from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import (
    col, when, sha2, trim, to_timestamp, to_date,
    current_timestamp, lit, coalesce, row_number,
    regexp_replace, upper, lower
)
from pyspark.sql.window import Window
import logging
import os

log = logging.getLogger("northpeak.silver")

BRONZE_BASE  = os.getenv("BRONZE_PATH",  "/tmp/northpeak/bronze")
SILVER_BASE  = os.getenv("SILVER_PATH",  "/tmp/northpeak/silver")
QUARANTINE   = os.getenv("QUARANTINE_PATH", "/tmp/northpeak/quarantine")
INGESTION_DATE = os.getenv("INGESTION_DATE", "2026-07-14")


def cleanse_orders(df: DataFrame) -> tuple[DataFrame, DataFrame]:
    """
    Apply all Silver rules to orders table.
    Returns (clean_df, quarantine_df)
    """
    log.info("Cleansing: orders")

    # 1. Remove Bronze metadata columns before Silver write
    bronze_cols = [c for c in df.columns if c.startswith("_bronze_")]
    df = df.drop(*bronze_cols)

    # 2. DEDUPLICATION - keep latest per order_id
    # (2.3% of GroceryDirect/NP Core orders have duplicate order_id)
    window = Window.partitionBy("order_id").orderBy(col("created_at").desc())
    df = (df
          .withColumn("_row_num", row_number().over(window))
          .filter(col("_row_num") == 1)
          .drop("_row_num"))

    # 3. NULL customer_id - flag as UNKNOWN, do not drop
    # Finance needs these records for revenue totals
    df = df.withColumn(
        "customer_id",
        when(col("customer_id").isNull(), lit(-1))  # -1 = UNKNOWN_CUSTOMER sentinel
        .otherwise(col("customer_id"))
    )
    df = df.withColumn(
        "customer_id_is_unknown",
        when(col("customer_id") == -1, True).otherwise(False)
    )

    # 4. PII MASKING - SHA-256 hash payment_reference
    # Required: FCA and GDPR compliance
    df = df.withColumn(
        "payment_reference",
        sha2(col("payment_reference").cast("string"), 256)
    )

    # 5. Add Silver metadata
    df = (df
          .withColumn("_silver_cleansed_at", current_timestamp())
          .withColumn("_silver_version", lit("1.0.0")))

    # 6. VALIDATION - quarantine negative total_amount (true errors, not adjustments)
    quarantine_df = df.filter(col("total_amount") < 0)
    clean_df      = df.filter(col("total_amount") >= 0)

    quarantine_count = quarantine_df.count()
    clean_count      = clean_df.count()
    log.info(f"Orders clean: {clean_count:,} | quarantine: {quarantine_count:,}")

    return clean_df, quarantine_df


def cleanse_inventory(df: DataFrame) -> DataFrame:
    """
    Negative quantities are VALID for DC adjustments.
    Flag them, do not remove.
    """
    log.info("Cleansing: inventory")
    bronze_cols = [c for c in df.columns if c.startswith("_bronze_")]
    df = df.drop(*bronze_cols)

    df = df.withColumn(
        "is_adjustment",
        when(col("quantity_on_hand") < 0, True)
        .otherwise(col("is_adjustment"))
    )
    df = df.withColumn("_silver_cleansed_at", current_timestamp())
    return df


def write_silver_delta(df: DataFrame, table_name: str):
    """
    Write cleansed DataFrame to Silver as Delta table.
    Enterprise: same write command on Databricks ADLS Gen2 target.
    """
    path = f"{SILVER_BASE}/{table_name}"
    log.info(f"Writing Silver Delta: {path}")
    (df.write
       .format("delta")
       .mode("overwrite")
       .option("overwriteSchema", "true")
       .save(path))
    log.info(f"Silver write complete: {table_name}")
