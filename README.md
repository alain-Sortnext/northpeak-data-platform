# NorthPeak Retail Group - Data Platform Engineering

**Project Lab | Mid-Senior Data Engineer Simulation**

---

## Business Context

NorthPeak Retail Group Ltd is a fictional UK grocery retailer (inspired by Tesco, Ocado, ASOS) with:
- 247 supermarkets across England, Scotland and Wales
- 5 disconnected source systems from acquisitions (2018-2023)
- A £20.8M annual cost from broken data integration
- A hard platform deadline of 31 December 2026

You join as a **Data Engineer** on the Data Platform Engineering team. Your job is to build the enterprise data platform from scratch.

---

## Repository Structure

```
northpeak-data-platform/
├── architecture/           Phase 1 - ADR, diagrams, cloud mapping
├── source_database/        Phase 2 - PostgreSQL DDL and seed data
├── ingestion/              Phase 3 - PySpark medallion pipeline
├── airflow/                Phase 4 - Orchestration DAGs
├── dbt/                    Phase 5 - Transformation models
├── quality/                Phase 6 - Great Expectations + pytest
├── terraform/              Phase 8 - Infrastructure as code
├── governance/             Phase 6 - Data contracts
├── monitoring/             Phase 6 - Observability
├── incidents/              Phase 8 - RCA documentation
├── submissions/            All phase written submissions
└── docs/                   Data dictionary and reference docs
```

---

## Tech Stack

| Layer | Tool | Enterprise Equivalent |
|-------|------|-----------------------|
| Source DB | PostgreSQL 14 | Production PostgreSQL |
| Processing | PySpark 3.5 (local) | Databricks Runtime |
| Table format | Delta Lake OSS | Databricks Delta Lake |
| Warehouse | DuckDB | Snowflake / Azure Synapse |
| Orchestration | Apache Airflow 2.9 | Databricks Workflows / MWAA |
| Transformation | dbt Core 1.8 | dbt Cloud |
| Testing | pytest | Enterprise pytest |
| Data quality | Great Expectations | Monte Carlo / Acceldata |
| CI/CD | GitHub Actions | Azure DevOps / Jenkins |
| IaC | Terraform 1.8 | Azure / AWS full deployment |

---

## Simulation Phases

| Phase | Sprint | Deliverable |
|-------|--------|-------------|
| Phase 1 | Sprint 0 | Architecture + ADR + User Stories |
| Phase 2 | Sprint 1 | PostgreSQL Source Schema + Seed Data |
| Phase 3 | Sprint 2 | PySpark Medallion Pipeline |
| Phase 4 (GATE) | Sprint 3 | Airflow DAG + GitHub Actions CI/CD + pytest |
| Phase 5 | Sprint 4 | dbt Transformations + SQL Optimisation |
| Phase 6 | Sprint 5 | Great Expectations + Data Contracts + Observability |
| Phase 7 | Sprint 6 | Engineering Review + Technical Assessment |
| Phase 8 | Sprint 7 | Production Runbook + Terraform + Incident RCA |

---

## Salary Targets This Simulation Prepares You For

| Market | Mid Level | Senior Level |
|--------|-----------|--------------|
| UK | 55,000 - 70,000 GBP | 70,000 - 95,000 GBP |
| USA | $110,000 - $141,000 | $141,000 - $218,000 |
| Canada | CA$100,000 - CA$130,000 | CA$130,000 - CA$162,000 |

*Sources: Reed.co.uk, Glassdoor UK/US/CA, Tesco Careers, ZipRecruiter Toronto - July 2026*

---

*Classification: Internal - Data Engineering Team Only*
*Document version: 1.0 | Project Lab | July 2026*
