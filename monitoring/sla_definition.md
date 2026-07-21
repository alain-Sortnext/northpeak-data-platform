# NorthPeak Data Platform - SLA Definition

**Version:** 1.0.0
**Owner:** Data Platform Engineering Team
**Effective from:** 14 July 2026

---

## Pipeline SLAs

| Layer | Table | Expected Available By | Alert Threshold | Escalation |
|-------|-------|-----------------------|-----------------|------------|
| Bronze | All tables | 03:30 UTC | 03:45 UTC | Page on-call |
| Silver | orders, inventory | 04:30 UTC | 04:45 UTC | Page on-call |
| Gold | fact_sales | 06:00 UTC | 06:15 UTC | Page CTO |
| Gold | fact_inventory | 06:30 UTC | 06:45 UTC | Page on-call |
| Gold | fact_loyalty_points | 07:00 UTC | 07:15 UTC | Slack alert only |

## Data Quality SLAs

| Check | Threshold | Action on Breach |
|-------|-----------|-----------------|
| Null order_id | 0% | Block Silver write, alert immediately |
| Duplicate order_id in Silver | 0% | Block downstream, quarantine, alert |
| Unknown customer rate | Less than 6% | Warn only (expected ~4.1%) |
| Negative total_amount in Gold | 0% | Fail pipeline immediately |
| Bronze row count below 100 daily | 0% | Alert and block Silver |
| fact_sales freshness | Less than 25 hours | dbt source freshness error |

## Observability Metrics

Tracked daily in monitoring dashboard:

- Bronze row counts per table per source system
- Silver deduplication rate (rows removed)
- Silver quarantine rate (rows failed validation)
- Gold fact_sales daily row count
- Pipeline run duration (target less than 2 hours end-to-end)
- Data freshness (hours since last successful load)
