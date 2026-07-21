# NorthPeak Data Pipeline - Process Notes
## Author: Dmitri Volkov | Last Updated: 10 July 2026
## WARNING: Stages 1-3 only documented. Stages 4-8 NOT DOCUMENTED.

---

## Stage 1: NP Core Extraction

### Connection Details
- Host: localhost (dev) / np-core-prod.northpeak.internal (prod)
- Port: 5432
- Database: np_core
- Schema: np_core
- User: pipeline_reader (read-only)
- Connection via: SQLAlchemy + psycopg2

### Tables Extracted (daily, full refresh for now - no incremental yet)
- np_core.orders (primary table - ORDER BY order_date)
- np_core.order_items
- np_core.customers
- np_core.products
- np_core.stores
- np_core.inventory
- np_core.stock_movements

### Column Notes
- `orders.customer_id` - NULLABLE. Pre-2018 in-store transactions have no customer link.
  Silver fix: map to UNKNOWN_CUSTOMER_ID = -1. Do NOT drop these rows - Finance needs them.
- `orders.payment_reference` - Contains card data for records before 2021-03-01.
  Silver fix: SHA-256 hash this column before writing to Silver.
- `inventory.quantity_on_hand` - CAN BE NEGATIVE. These are DC adjustment records.
  Silver fix: set is_adjustment = TRUE when quantity < 0. Do NOT treat as errors.
- `customers.email` - NULL for FreshMart migration batch (customer_id 401-470 approximately).
  Silver fix: flag as MISSING_EMAIL, do not impute.

### Known Issue - Column Naming
Pre-2018 tables (before FreshMart migration) use snake_case.
Post-FreshMart tables sometimes use camelCase or have extra prefixes.
Standardise ALL column names to snake_case in Silver.

---

## Stage 2: GroceryDirect Extraction

### Connection Details
- Type: MongoDB 6.0
- Connection string: mongodb://gd-reader:REDACTED@gd-prod.northpeak.internal:27017/grocerydirect
- Database: grocerydirect
- Collections: orders, returns, customers, delivery_slots

### Key Issue - Returns Not Linked
8.3% of return documents do NOT contain the original order_id.
They have a `basket_ref` field instead that SOMETIMES matches but not always.
CHECK THIS - Yemi says it is causing double-counting in revenue reports.

### Key Issue - Nested JSON
order.line_items is a nested array. Explode this to row-per-item in Bronze.
Do NOT flatten at source - keep raw nested JSON in Bronze, explode in Silver.

---

## Stage 3: SupplyLink Extraction

### Connection Details
- Type: SQL Server 2019
- Host: supplylink-prod.northpeak.internal
- Port: 1433
- Database: SupplyLinkProd
- Schema: dbo
- IMPORTANT: Use pyodbc + ODBC Driver 18 for SQL Server

### CRITICAL KNOWN ISSUE - SKU Silent Failures
The SupplyLink-to-EPOS handoff is failing silently for approximately 14% of SKUs.
Stock is received at DC and scanned into SupplyLink but never appears in NP Core inventory.
Marcus Webb is aware. Root cause investigation is SEPARATE ticket - NP-DATA-847.
DO NOT fix this in the pipeline - just flag it. The is_epos_synced field is your clue.
CHECK THIS with Marcus before touching anything.

### CRITICAL KNOWN ISSUE - Timezone
event_timestamp in SupplyLink alternates between UTC and BST with no consistent flag.
Pattern: UTC in winter months (Oct-Mar), BST in summer months (Apr-Sep) - but NOT reliable.
Silver fix: assume UTC for all Oct-Mar records, add 1hr for Apr-Sep. Document assumption.
This needs a proper fix in a future sprint.

### Column Shorthand (not self-explanatory)
- MVT_TYPE: movement type code. See glossary in company_brief.md
  - RCT = receipt from supplier
  - TRF = inter-DC transfer
  - ADJ = inventory adjustment (can produce negative quantities)
  - WOF = write-off
  - RTN = customer return processed at DC
- IS_CONF: is_confirmed - whether movement confirmed by warehouse manager
- DC_REF: DC internal reference, NOT the supplier delivery reference

---

## Stage 4 onwards: NOT DOCUMENTED

I ran out of time before leaving. The following are NOT documented:
- Stage 4: RewardsCo API extraction (pagination, rate limiting)
- Stage 5: NP Financial extraction (FCA boundary, read replica setup)
- Stage 6: Bronze to Silver transformation logic
- Stage 7: Silver to Gold / dbt setup
- Stage 8: Airflow DAG configuration

### What I Know That Is Not Written Down
- RewardsCo API key is in LastPass under "NorthPeak Integrations" - ask Aisha
- The FCA read replica requires VPN + certificate - IT ticket NP-IT-2341 has details
- The Airflow Docker setup is on my local machine - I'll send you the docker-compose.yml

### Open Questions (you need to answer these)
1. How do we handle late-arriving GroceryDirect returns? No SLA agreed with the business.
2. What is the correct grain for FactSales? Order-level or order-item-level? Yemi has opinions.
3. RewardsCo API - do we need historical backfill or just forward from go-live? Ask Marcus.
4. NP Financial: which tables exactly? Legal said minimum data principle applies.

### Contacts
- Aisha Okafor (your manager) - architecture decisions, tool choices
- Marcus Webb (Head of Data) - business requirements, NP Financial scope
- Yemi Adeyemi (Analytics Engineer) - dbt consumer requirements, FactSales grain
- Chloe Tan (BI Developer) - Power BI requirements, what columns she needs
- Barry Higgins (SupplyLink admin, IT) - SQL Server connection issues

---
Last updated: Dmitri Volkov | 10 July 2026 | Stage 3 only
