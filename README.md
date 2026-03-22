# Texas Procurement Watch (TX_BID_WATCH)

A serverless AWS data engineering pipeline that ingests Texas procurement data, stores versioned raw snapshots in S3, and builds a curated analytics layer using Athena and Parquet.


## Overview
This project implements an end-to-end data pipeline on AWS that:
- Ingests procurement data from the Texas Open Data Portal (Socrata API)
- Stores timestamped raw snapshots in S3 (data lake “raw zone”)
- Makes raw data queryable via Athena + Glue
- Transforms raw data into a curated Parquet analytics layer
- Automates incremental raw to curated processing using a second Lambda
- Sends notifications and monitors pipeline health
The pipeline is fully deployed and managed using Terraform.

## Architecture
EventBridge (daily schedule) -> Lambda (Ingest) -> S3 (Raw Zone - NDJSON, partitioned) -> Athena / Glue (Raw Table) -> Lambda (Curate) -> Athena INSERT INTO -> S3 (Curated Zone - Parquet, partitioned) -> Athena (Curated Table)

## Pipeline Steps
1. Data Ingestion (Socrata API)
- Source: Texas Open Data (data.texas.gov)
- Dataset: qh8x-rm8r
- Pulls records updated within a 24-hour time window
- services/ingest/src/soda_client.py

2. Orchestrates Ingest Runs
Each run:
- Loads configuration from environment variables
- Fetches updated records
- Generates a UTC run timestamp (run_ts)
- Writes output to S3 
- services/ingest/src/watch.py

3. Raw Data Lake (S3)
Raw data is stored as NDJSON (one record per line) to make queryable in Athena using Hive-style partitions:
```bash
raw/
  dataset=qh8x-rm8r/
    run_date=YYYY-MM-DD/
      run_ts=YYYYMMDDTHHMMSSZ/
        data.json
```
4. Serverless Execution (Lambda)
- Ingest Lambda
- Entry point: handler.lambda_handler
- Executes ingest run
- Writes to S3
- Triggers downstream processing
- Sends SNS notification
- services/ingest/src/handler.py

5. Scheduled Automation (EventBridge)
- Runs every 24 hours
- No manual intervention required
- Fully serverless
- infra/terraform/eventbridge.tf

6. Raw Data Querying (Athena + Glue)
- Raw S3 data exposed via external table

7. Curated Data Layer (Parquet)
- A second layer transforms raw data into analytics-ready format: curated/bid_items/
- Format: Parquet, Partitioned by run_date
- Transformation includes: Type casting (string → numeric), Timestamp parsing, Selection of relevant columns

8. Incremental Curation (Lambda → Athena)
A second Lambda (tx-bid-watch-curate) performs:
- Pre-check: does this run already exist?
- If not: Executes INSERT INTO ... SELECT from raw → curated
- If yes: Skips (duplicate-safe)
- services/ingest/src/curate_handler.py

9. End-to-End Orchestration
The pipeline is fully connected:
- Ingest Lambda -> writes raw -> invokes Curate Lambda -> updates curated layer
- Triggered automatically after each ingest
- Asynchronous Lambda-to-Lambda invocation

10. Notifications (SNS)
After each run, you receive an email with:
- Dataset ID
- Run timestamp
- Rows ingested
- S3 output location

11. Observability (CloudWatch)
Alarms configured for:
- Lambda errors
- High execution duration
Logs available for:
- Debugging runs
- Inspecting outputs

## Tech Stack
- Python 3.12
- AWS Lambda
- AWS S3
- AWS EventBridge
- AWS SNS
- AWS Glue Data Catalog
- AWS Athena
- AWS CloudWatch
- Terraform (IaC)
- Socrata Open Data API (data.texas.gov)

## S3 Data Layout
```bash
<bucket>/
  raw/               # NDJSON source data
  curated/           # Parquet analytics layer
  athena-results/    # Athena query outputs
```

## Local Development
1. Create virtual environment:
   python3 -m venv .venv
   source .venv/bin/activate
2. Install dependencies:
   pip install -r requirements.txt
3. Run ingestion locally:
   python -m scripts.local_run

## Quickstart (Local)
1. Create a virtual environment and install deps:
```bash
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    cp .env.example .env
    python -m scripts.local_run 
```