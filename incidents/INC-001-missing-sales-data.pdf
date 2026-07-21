# Incident Report: INC-001 - FactSales Missing 3 Days of Data

**Incident ID:** INC-001
**Severity:** P1 - Critical
**Status:** Resolved
**Reported by:** Chloe Tan (BI Developer)
**Date reported:** 2026-10-15 08:47 UTC
**Date resolved:** 2026-10-15 14:22 UTC
**Duration:** 5 hours 35 minutes
**Affected tables:** marts.fact_sales
**Missing data:** 2026-10-12, 2026-10-13, 2026-10-14 (3 days)

---

## 1. Business Impact

The Power BI trading dashboard showed no sales data for 12-14 October 2026.
Chloe Tan reported this to the team after the trading director asked for a daily revenue figure at the 09:00 standup.
Finance could not produce the daily revenue report.

**Revenue at risk of misreporting:** approximately £1.2M across 3 days (estimated from prior week average).

---

## 2. Timeline

| Time (UTC) | Event |
|------------|-------|
| 2026-10-12 06:45 | Airflow DAG northpeak_daily_sales shows SUCCESS but dbt_test_gold_models task failed silently (exit code 1 not propagated) |
| 2026-10-13 06:40 | Same failure repeats - not noticed |
| 2026-10-14 06:38 | Same failure repeats - not noticed |
| 2026-10-15 08:47 | Chloe Tan reports missing data to engineering team |
| 2026-10-15 08:55 | On-call engineer (YOU) picks up incident |
| 2026-10-15 09:10 | Investigation starts: Airflow logs reviewed |
| 2026-10-15 09:35 | Root cause identified: dbt test failure not propagating exit code to Airflow |
| 2026-10-15 10:00 | Fix deployed to DAG (trigger_rule changed, exit code handling fixed) |
| 2026-10-15 10:15 | Backfill triggered for 3 missing dates |
| 2026-10-15 14:22 | Backfill complete, data validated, incident resolved |

---

## 3. Root Cause Analysis

**Root cause:** The `dbt_test_gold_models` BashOperator was using `bash_command` without `pipefail`, meaning a non-zero exit code from dbt test was swallowed by the shell. Airflow marked the task as SUCCESS because the bash wrapper returned 0.

**Why not detected immediately:** The monitoring dashboard only checked DAG run status (SUCCESS/FAILED), not task-level exit codes. A green DAG run was treated as data-available.

**Contributing factor:** No row count validation after dbt run. If we had checked that fact_sales received at least N rows for the execution date, the failure would have been caught within minutes of the 06:00 run completing.

**Wrong direction trap:** Initial investigation suspected a source system outage (NP Core). The PostgreSQL connection logs were clean. Wasted 20 minutes before pivoting to the Airflow task logs.

---

## 4. Resolution

1. Fixed BashOperator bash_command to use `set -e` and `set -o pipefail`
2. Added `on_failure_callback` to send PagerDuty alert on any task failure
3. Added post-dbt row count validation task to the DAG
4. Backfilled 3 missing dates using `airflow dags backfill`

---

## 5. Prevention Actions

| Action | Owner | Due Date | Status |
|--------|-------|----------|--------|
| Add row count validation task after all dbt runs | Data Platform Team | 2026-10-22 | Done |
| Add PagerDuty integration to all P1-severity DAG failures | Data Platform Team | 2026-10-22 | Done |
| Update monitoring dashboard to show task-level status | Data Platform Team | 2026-10-29 | In Progress |
| Add Great Expectations freshness check post-dbt | Data Platform Team | 2026-10-29 | To Do |
| Document backfill runbook step in production_runbook.md | Data Platform Team | 2026-10-29 | To Do |

---

## 6. Lessons Learned

- **Never trust DAG-level SUCCESS alone.** Always validate data presence, not just execution status.
- **BashOperator exit code handling is a known footgun.** Use `set -e -o pipefail` in every bash_command.
- **Monitoring must check data, not process.** A pipeline that runs but produces no data is a failure even if the DAG is green.
- **The wrong direction trap in investigation:** always check Airflow task logs before assuming source system failure.
