# NorthPeak Data Platform - Production Runbook

**Version:** 1.0.0
**Owner:** Data Platform Engineering Team
**Last updated:** 14 July 2026
**Emergency contact:** Aisha Okafor (Data Engineering Manager)

---

## 1. Daily Operations Checklist

Start of day (09:00 UTC):

- [ ] Check Airflow DAG status at http://airflow.northpeak.internal:8080
- [ ] Verify fact_sales row count for yesterday is greater than 100
- [ ] Check Great Expectations checkpoint report for any failing expectations
- [ ] Review quarantine table row count (should be less than 1% of total)
- [ ] Confirm Power BI dashboard shows data for yesterday

---

## 2. Common Incident Scenarios

### Scenario A: FactSales missing data for a date

**Symptoms:** Power BI shows blank for a date. Chloe Tan will message you.

**Investigation steps:**
1. Check Airflow DAG run for that date: was it SUCCESS or FAILED?
2. If SUCCESS: check task-level logs for `dbt_test_gold_models` (known issue - see INC-001)
3. If FAILED: check which task failed and read the log
4. Check Bronze partition exists: `ls /bronze/np_core/orders/_bronze_ingestion_date=YYYY-MM-DD/`
5. Check Silver: `SELECT COUNT(*) FROM silver.orders WHERE DATE(order_date) = 'YYYY-MM-DD'`
6. Check Gold: `SELECT COUNT(*) FROM marts.fact_sales WHERE DATE(order_date) = 'YYYY-MM-DD'`

**Fix - backfill:**
```bash
airflow dags backfill northpeak_daily_sales \
  -s 2026-10-12 \
  -e 2026-10-14 \
  --reset-dagruns
```

**SLA:** Resolve within 4 hours of detection. Escalate to Aisha if not resolved in 2 hours.

---

### Scenario B: Bronze row count anomaly (too low)

**Symptoms:** Bronze row count alert fires. Less than 100 orders ingested for the date.

**Investigation steps:**
1. Check NP Core PostgreSQL connectivity: `psql -h np-core-prod.northpeak.internal -U pipeline_reader -d np_core -c "SELECT COUNT(*) FROM np_core.orders WHERE DATE(order_date) = CURRENT_DATE;"`
2. Check SupplyLink SQL Server connectivity via pyodbc
3. Check RewardsCo API health: `curl -H "Authorization: Bearer $REWARDSCO_API_KEY" https://api.rewardsco.com/v2/health`
4. Review weeks 38-40 anomaly pattern documented in process notes (known historical dip)

**Do NOT:** Assume low volume is a data quality error without checking source system first.

---

### Scenario C: dbt test failure

**Symptoms:** Airflow dbt_test_gold_models task fails. Email alert fires.

**Investigation steps:**
1. Read the dbt test output: `cat /opt/northpeak/dbt/target/run_results.json`
2. Identify which test failed and which model it applies to
3. Common failures and fixes:

| Failing test | Likely cause | Fix |
|-------------|-------------|-----|
| assert_fact_sales_no_null_store_key | New store in NP Core not in DimStore | Run `dbt run --models dim_store` first |
| expect unique order_id | Dedup failed in Silver | Check silver_cleansing.py dedup logic |
| freshness error on silver.orders | Silver pipeline failed or ran late | Rerun silver_cleanse_orders task |

---

## 3. Backfill Procedure

**Use this when:** Missing data detected for one or more historical dates.

```bash
# Step 1: Identify missing dates
SELECT date_day 
FROM marts.dim_date 
WHERE date_day >= '2026-10-01' 
  AND date_day NOT IN (SELECT DISTINCT DATE(order_date) FROM marts.fact_sales)
ORDER BY date_day;

# Step 2: Run backfill for missing range
airflow dags backfill northpeak_daily_sales \
  -s YYYY-MM-DD \
  -e YYYY-MM-DD \
  --reset-dagruns

# Step 3: Validate after backfill
SELECT DATE(order_date), COUNT(*) as order_count
FROM marts.fact_sales
WHERE DATE(order_date) BETWEEN 'YYYY-MM-DD' AND 'YYYY-MM-DD'
GROUP BY DATE(order_date)
ORDER BY DATE(order_date);
```

---

## 4. Key Contacts

| Role | Name | Contact | When to contact |
|------|------|---------|----------------|
| Data Engineering Manager | Aisha Okafor | aisha.okafor@northpeak.co.uk | P1 incidents, all architecture decisions |
| Head of Data Platform | Marcus Webb | marcus.webb@northpeak.co.uk | Escalation if Aisha unavailable |
| BI Developer (dashboard) | Chloe Tan | chloe.tan@northpeak.co.uk | Dashboard issues, Power BI questions |
| Analytics Engineer | Yemi Adeyemi | yemi.adeyemi@northpeak.co.uk | dbt model questions, Gold layer issues |
| SupplyLink admin | Barry Higgins (IT) | barry.higgins@northpeak.co.uk | SQL Server connection issues only |

---

## 5. Credential Locations

**NEVER commit credentials to GitHub.**

| Credential | Location |
|-----------|---------|
| NP Core DB password | Azure Key Vault: northpeak-kv / secret: np-core-db-pass |
| RewardsCo API key | Azure Key Vault: northpeak-kv / secret: rewardsco-api-key |
| NP Financial read replica cert | IT ticket NP-IT-2341, stored in Key Vault |
| Airflow admin password | LastPass: "NorthPeak Airflow Admin" |

---

## 6. Deployment Procedure (new pipeline changes)

```bash
# Step 1: Branch from main
git checkout -b feature/NP-DATA-XXX-description

# Step 2: Make changes, write tests
pytest quality/pytest/ -v

# Step 3: Push and open PR
git push origin feature/NP-DATA-XXX-description
# GitHub Actions runs pytest automatically on PR

# Step 4: PR must pass all checks before merge
# - pytest: all tests green
# - dbt compile: no syntax errors
# - Great Expectations: suite validates

# Step 5: Merge to main triggers deployment to dev
# Step 6: Manual promotion to prod after QA sign-off (Aisha)
```
