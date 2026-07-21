# NorthPeak Data Platform - Data Dictionary

**Version:** 1.0.0 | **Last updated:** 14 July 2026

---

## Bronze Layer Tables

### bronze.np_core_orders
| Column | Type | Source | Notes |
|--------|------|--------|-------|
| order_id | INTEGER | np_core.orders | Primary key |
| order_ref | VARCHAR(30) | np_core.orders | Format: NP-YYYY-NNNNNNN |
| customer_id | INTEGER | np_core.orders | NULLABLE - 4.1% null (pre-2018) |
| store_id | INTEGER | np_core.orders | Always populated |
| order_channel | VARCHAR(20) | np_core.orders | in_store, online, click_collect |
| total_amount | NUMERIC(10,2) | np_core.orders | Gross GBP before discount |
| payment_reference | VARCHAR(100) | np_core.orders | CONTAINS PII - mask in Silver |
| _bronze_ingested_at | TIMESTAMP | Pipeline | When Bronze write completed |
| _bronze_ingestion_date | DATE | Pipeline | Partition key |

### bronze.sl_movements (SupplyLink DC movements)
| Column | Type | Source | Notes |
|--------|------|--------|-------|
| movement_id | INTEGER | SupplyLink | Primary key |
| dc_code | VARCHAR(20) | SupplyLink | DC-BHAM, DC-LEEDS etc |
| sku | VARCHAR(50) | SupplyLink | Links to np_core.products.sku |
| movement_type | VARCHAR(30) | SupplyLink | RCT=receipt, TRF=transfer, ADJ=adjustment |
| movement_date | VARCHAR(20) | SupplyLink | MIXED FORMAT - YYYY-MM-DD or DD/MM/YYYY |
| timezone | VARCHAR(5) | SupplyLink | MIXED UTC/BST - normalise in Silver |
| reached_epos | VARCHAR(1) | SupplyLink | Y or NULL. NULL = silent failure (14% of records) |

---

## Silver Layer Tables

### silver.orders
All Bronze orders columns PLUS:
| Column | Type | Notes |
|--------|------|-------|
| customer_id_is_unknown | BOOLEAN | TRUE when original customer_id was null |
| payment_reference | VARCHAR(64) | SHA-256 hash of original (PII removed) |
| _silver_cleansed_at | TIMESTAMP | When Silver write completed |
| _silver_version | VARCHAR(10) | Pipeline version that created this record |

---

## Gold Layer Tables

### marts.fact_sales
| Column | Type | Notes |
|--------|------|-------|
| sales_key | VARCHAR(64) | Surrogate key - SHA-256 of order_id |
| order_id | INTEGER | Natural key from NP Core |
| customer_key | INTEGER | FK to dim_customer. -1 = UNKNOWN |
| store_key | INTEGER | FK to dim_store. Never null |
| date_key | INTEGER | FK to dim_date. Format: YYYYMMDD |
| total_amount | NUMERIC(10,2) | Gross GBP |
| net_amount | NUMERIC(10,2) | total_amount minus discount_amount |
| order_channel | VARCHAR(20) | Degenerate dimension |
| loyalty_points_earned | INTEGER | From NP Core |

---

## SupplyLink Column Shorthand Glossary

| Code | Full Name | Description |
|------|-----------|-------------|
| RCT | Receipt | Stock received from supplier at DC |
| TRF | Transfer | Stock moved between DCs |
| ADJ | Adjustment | Manual inventory correction (can be negative) |
| WOF | Write-off | Damaged/expired stock removed |
| RTN | Return | Customer return processed at DC |
| IS_CONF | is_confirmed | Warehouse manager sign-off flag |
| DC_REF | DC Reference | Internal DC tracking number (not supplier ref) |
| MVT_TYPE | Movement Type | See above codes |
