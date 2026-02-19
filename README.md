# tx_bid_watch

A serverless AWS data pipeline that ingests procurement bid data from the Texas Open Data Portal, stores raw snapshots in S3, and sends keyword-based alerts when new matching bids are detected. (Work in progress)


## Problem
Public procurement data is available via open data portals, but there is not an automated way to monitor new data in bid opportunities in real time.

This project builds a lightweight data engineering pipeline that:
- Ingests data from data.texas.gov
- Stores historical snapshots in S3
- Identifies new bid items matching defined keywords
- Sends notifications when relevant items appear

## Overview
EventBridge (schedule)
    ↓
Lambda ingestion job
    ↓
S3 (raw storage)
    ↓
Keyword filtering logic
    ↓
SNS email alert

## Tech Stack
- Python 3.12
- AWS Lambda
- AWS S3
- AWS EventBridge
- AWS SNS
- Terraform (Infrastructure as Code)
- Socrata Open Data API (data.texas.gov)

## Local Development
1. Create virtual environment:
   python3 -m venv .venv
   source .venv/bin/activate
2. Install dependencies:
   pip install -r requirements.txt
3. Run ingestion locally:
   python scripts/local_run.py

