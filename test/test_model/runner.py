"""Early example of testing query generation on a live db.

Minimal start - not the most usable but demonstrates the idea.

Assumes the following env vars are set:
    - BITIO_KEY -> a bit.io API key with appropriate access to any dbs in the test suite
    - OPENAI_API_KEY -> an OpenAI API key for calling the completions endpoint
"""
import csv
import json
import os
import typing as t
import uuid
from datetime import datetime

import bitdotio
import structlog

from pg_text_query import (
    get_db_schema, get_default_prompt, generate_query, is_valid_query, QueryGenError
)
from pg_text_query.gen_query import DEFAULT_COMPLETION_CONFIG

logger = structlog.getLogger()


TEST_PATH = "test/test_model"
TEST_SUITES_PATH = os.path.join(TEST_PATH, "test_suites")
RESULTS_PATH = os.path.join(TEST_PATH, "test_results")
RESULT_HEADER = ["timestamp", "test_suite", "test_id", "db_name", "text", "prompt", "query", "valid", "success"]

b = bitdotio.bitdotio(os.getenv("BITIO_KEY"))


def run_suite(suite: t.Dict[str, t.Any], filename: str, results_writer: t.Any) -> None:
    suite_results = []

    db_name = suite["db_name"]

    # Extract a structured db schema from Postgres
    with b.pooled_cursor(db_name) as cur:
        db_schema = get_db_schema(cur, suite["db_name"])

    success_count = 0
    for test_case in suite["test_cases"]:
        test_id = test_case["id"]
        text = test_case["text"]
        
        # Generate prompt
        prompt = get_default_prompt(test_case["text"], db_schema)
        log_args = {"test_id": test_id, "db_name": db_name, "text": text, "prompt": prompt}
        logger.info("generated test prompt", **log_args)

        # Generate query w/o validation
        query = generate_query(prompt)
        log_args["query"] = query
        logger.info("generated test query", **log_args)

        # Validate query
        valid = is_valid_query(query)
        log_args["valid"] = valid
        logger.info("validated query", **log_args)

        success = False
        if valid:
            try:
                with b.pooled_cursor(db_name) as cur:
                    cur.execute(query)
                    result = [list(record) for record in cur.fetchall()]
                    result = result if test_case["ordered"] else sorted(result)
                    expected = test_case["expected_records"] if test_case["ordered"] else sorted(test_case["expected_records"])
                    success = result == expected
                    if not success:
                        log_args["expected_records"] = expected
                        log_args["actual_records"] = result
            except Exception:
                logger.exception("error when executing generated query", **log_args)
        
        log_args["success"] = success
        logger.info("executed query", **log_args)

        # Record result
        results_writer.writerow([
            str(datetime.now()),
            filename,
            test_id,
            db_name,
            text,
            prompt,
            query,
            valid,
            success,
        ])
        success_count += int(success)
    logger.info(f"finished test suite with {success_count} of {len(suite['test_cases'])} successful", **log_args)


def main() -> None:
    # Create a results directory for this run
    RESULTS_PATH = os.path.join(TEST_PATH, "test_results", f"{str(datetime.now())}-{uuid.uuid4()}")
    os.makedirs(RESULTS_PATH)
    # Stash model config for run
    with open(os.path.join(RESULTS_PATH, "model_config.json"), "w") as f:
        json.dump(DEFAULT_COMPLETION_CONFIG, f)

    with open(os.path.join(RESULTS_PATH, "test_results.csv"), "w") as f:
        result_writer = csv.writer(f, quoting=csv.QUOTE_ALL)
        result_writer.writerow(RESULT_HEADER)
        for filename in os.listdir(os.path.join(TEST_PATH, "test_suites")):
            with open(os.path.join(TEST_PATH, "test_suites", filename)) as f:
                # Should add error handling/validation
                suite = json.load(f)
            run_suite(suite, filename, result_writer)
