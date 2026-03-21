from __future__ import annotations

import json
import os
import time
from typing import Any

import boto3

ATHENA_DATABASE = os.environ["ATHENA_DATABASE"]
ATHENA_WORKGROUP = os.environ.get("ATHENA_WORKGROUP", "primary")
ATHENA_OUTPUT = os.environ["ATHENA_OUTPUT"]
SNS_TOPIC_ARN = os.environ.get("SNS_TOPIC_ARN")

athena = boto3.client("athena")
sns = boto3.client("sns")


def start_query(sql: str) -> str:
    resp = athena.start_query_execution(
        QueryString=sql,
        QueryExecutionContext={"Database": ATHENA_DATABASE},
        ResultConfiguration={"OutputLocation": ATHENA_OUTPUT},
        WorkGroup=ATHENA_WORKGROUP,
    )
    return resp["QueryExecutionId"]


def wait_for_query(query_execution_id: str, poll_seconds: int = 2, timeout_seconds: int = 300) -> dict[str, Any]:
    waited = 0
    while True:
        resp = athena.get_query_execution(QueryExecutionId=query_execution_id)
        state = resp["QueryExecution"]["Status"]["State"]

        if state in {"SUCCEEDED", "FAILED", "CANCELLED"}:
            return resp

        time.sleep(poll_seconds)
        waited += poll_seconds
        if waited >= timeout_seconds:
            raise TimeoutError(f"Athena query timed out: {query_execution_id}")


def get_scalar_result(query_execution_id: str) -> str:
    resp = athena.get_query_results(QueryExecutionId=query_execution_id)
    rows = resp["ResultSet"]["Rows"]

    # rows[0] is header, rows[1] is first data row
    if len(rows) < 2:
        return "0"

    data = rows[1].get("Data", [])
    if not data:
        return "0"

    return data[0].get("VarCharValue", "0")


def publish_message(subject: str, message: str) -> None:
    if not SNS_TOPIC_ARN:
        return
    sns.publish(
        TopicArn=SNS_TOPIC_ARN,
        Subject=subject,
        Message=message,
    )


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    dataset = event["dataset"]
    run_date = event["run_date"]
    run_ts = event["run_ts"]

    check_sql = f"""
    SELECT count(*) AS existing_rows
    FROM tx_bid_watch.bid_items_curated
    WHERE dataset = '{dataset}'
      AND run_date = '{run_date}'
      AND run_ts = '{run_ts}'
    """

    check_qid = start_query(check_sql)
    check_status = wait_for_query(check_qid)
    check_state = check_status["QueryExecution"]["Status"]["State"]

    if check_state != "SUCCEEDED":
        reason = check_status["QueryExecution"]["Status"].get("StateChangeReason", "unknown")
        raise RuntimeError(f"Curated pre-check failed: {reason}")

    existing_rows = int(get_scalar_result(check_qid))

    if existing_rows > 0:
        result = {
            "status": "skipped",
            "reason": "run already exists in curated",
            "dataset": dataset,
            "run_date": run_date,
            "run_ts": run_ts,
            "existing_rows": existing_rows,
        }
        publish_message("TX Bid Watch curate skipped", json.dumps(result, indent=2))
        return result

    insert_sql = f"""
    INSERT INTO tx_bid_watch.bid_items_curated
    SELECT
      dataset,
      run_ts,

      project_id,
      project_number,
      control_section_job_csj,
      controlling_project_id_ccsj,
      bid_code,
      bid_item_code,
      bid_item_description,
      county,
      district_division,
      highway,
      let_type,
      project_classification,
      project_type,
      measurement_unit,
      measurement_unit_description,
      proposal_status,
      specification_description,

      bidder_prequalification_waiver,
      mandatory_pre_bidders,
      special_notification_txt,

      try_cast(bid_item_quantity AS double) AS bid_item_quantity_num,
      try_cast(try_cast(bid_item_sequence_number AS double) AS integer) AS bid_item_sequence_number_num,
      try_cast(try_cast(maximum_number_of_working AS double) AS integer) AS maximum_number_of_working_num,
      try_cast(proposal_guarantee_amount AS double) AS proposal_guarantee_amount_num,
      try_cast(sealed_engineer_s_estimate AS double) AS sealed_engineer_s_estimate_contract,
      try_cast(sealed_engineer_s_estimate_1 AS double) AS sealed_engineer_s_estimate_project,
      try_cast(spec_code AS double) AS spec_code_num,

      try(date_parse(bid_recieved_until_date_and, '%Y-%m-%dT%H:%i:%s.%f')) AS bid_received_until_ts,
      try(date_parse(bids_will_be_opened_date, '%Y-%m-%dT%H:%i:%s.%f')) AS bids_opened_ts,
      try(date_parse(project_approved_let_date, '%Y-%m-%dT%H:%i:%s.%f')) AS project_approved_let_ts,
      try(date_parse(project_estimated_let_date, '%Y-%m-%dT%H:%i:%s.%f')) AS project_estimated_let_ts,
      try(date_parse(proposal_published_date, '%Y-%m-%dT%H:%i:%s.%f')) AS proposal_published_ts,

      run_date
    FROM tx_bid_watch.bid_items_raw
    WHERE dataset = '{dataset}'
      AND run_date = '{run_date}'
      AND run_ts = '{run_ts}'
    """

    insert_qid = start_query(insert_sql)
    insert_status = wait_for_query(insert_qid)
    insert_state = insert_status["QueryExecution"]["Status"]["State"]

    if insert_state != "SUCCEEDED":
        reason = insert_status["QueryExecution"]["Status"].get("StateChangeReason", "unknown")
        raise RuntimeError(f"Curated insert failed: {reason}")

    result = {
        "status": "inserted",
        "dataset": dataset,
        "run_date": run_date,
        "run_ts": run_ts,
        "check_query_execution_id": check_qid,
        "insert_query_execution_id": insert_qid,
    }
    publish_message("TX Bid Watch curate succeeded", json.dumps(result, indent=2))
    return result