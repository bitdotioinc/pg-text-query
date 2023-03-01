import json
import os
import sys
import subprocess
from dotenv import load_dotenv
import logging
from pprint import pprint
import argparse

load_dotenv()


from prettytable import PrettyTable
from termcolor import colored

dirname = os.path.dirname(__file__)
test_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(test_dir)

# Add path to pg_text_query to system path
pg_text_query_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../")
print(pg_text_query_path)
sys.path.append(pg_text_query_path)
from pg_text_query import (
    get_db_schema,
    get_default_prompt,
    get_custom_prompt,
    generate_query,
    is_valid_query,
    QueryGenError,
    describe_database,
)
from pg_text_query.gen_query import DEFAULT_COMPLETION_CONFIG


def load_schema(schema_path):
    with open(schema_path) as f:
        schema = json.load(f)
    return schema


def format_sql(sql_code):
    cmd = ["pg_format", "-s2", "-g", "-n"]
    p = subprocess.Popen(
        cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    stdout, stderr = p.communicate(input=sql_code.encode())
    return stdout.decode().strip()


# Read the prompts, schemas, and expected outputs from a JSON file
with open(os.path.join(dirname, "test_prompts.json")) as f:
    data = json.load(f)


def get_test_data(category="easy"):
    prompts_file = os.path.join(root_dir, "test_prompts", "test_prompts.json")
    with open(prompts_file) as f:
        data = json.load(f)
        return data[category]


# Define a test function to test each prompt
def test_prompts(task_prompt, test_data, category="easy"):

    # Get the task prompt from the command line argument
    log_results = {"task_prompt": task_prompt, "results": []}

    counter = 0
    n_success = 0
    for test_case in get_test_data(category):
        id = test_case["id"]
        user_prompt = test_case["prompt"]
        expected_outputs = test_case["expected_outputs"]
        schema = test_case["schema"]

        # Load the schema from the JSON file
        schema_path = os.path.join(root_dir, "test_prompts", "test_schemas", schema)
        db_schema = load_schema(schema_path)
        prompt = get_custom_prompt(
            db_schema=db_schema, user_prompt=user_prompt, task_prompt=task_prompt
        )

        # Translate the prompt to SQL and validate the output
        sql_output = generate_query(prompt)
        assert sql_output is not None, f"Generated SQL code is None: prompt={prompt}"
        # assert is_valid_query(sql_output), f"Generated SQL code is not valid: prompt={prompt}, sql_output={sql_output}"

        # Check if any of the expected outputs match the generated output
        success = False
        for expected_output in expected_outputs:
            if format_sql(sql_output) == format_sql(expected_output):
                success = True
                break

        # Log the result
        if success:
            log_message = f"{id} - SUCCESS - Task: {task_prompt} - User prompt: {user_prompt} - Generated SQL: {format_sql(sql_output)} - Expected SQL: {format_sql(expected_output)}"
            logging.info(log_message)
            n_success += 1
            counter += 1
        else:
            log_message = f"{id} - FAILURE - Task: {task_prompt} - User prompt: {user_prompt} - Generated SQL: {format_sql(sql_output)} - Expected SQL: {expected_outputs}"
            logging.error(log_message)
            counter += 1

        result = {
            "id": id,
            "user_prompt": user_prompt,
            "task_prompt": task_prompt,
            "prompt": prompt,
            "expected_outputs": expected_outputs,
            "sql_output": sql_output,
            "success": success,
        }

        log_results["results"].append(result)

    log_results.update({"total": counter, "successful": n_success})
    pprint(log_results)
    return log_results


if __name__ == "__main__":

    # Define command-line arguments
    parser = argparse.ArgumentParser(description="Text to SQL Translation Test Suite")
    parser.add_argument(
        "--task",
        "-t",
        dest="task_prompt",
        type=str,
        help="The task prompt to be tested with various user prompts",
    )
    parser.add_argument(
        "--category",
        "-c",
        dest="category",
        type=str,
        help="The test category (e.g. 'easy', 'medium', 'hard')",
    )
    parser.add_argument("--log-file", "-l", type=str, dest="log_file", help="The name of the log file")
    args = parser.parse_args()

    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        filename=args.log_file,
    )

    # Test the prompts for the specified task
    results = test_prompts(
        task_prompt=args.task_prompt, test_data=data, category=args.category
    )

    table = PrettyTable()
    table.field_names = ["ID", "User Prompt", "Generated SQL", "Expected SQL", "Result"]
    for result in results["results"]:
        row = [
            result["id"],
            result["user_prompt"],
            result["sql_output"].strip(),
            result["expected_outputs"],
            "SUCCESS" if result["success"] else "FAILURE",
        ]
        color = "green" if result["success"] else "red"
        table.add_row([colored(field, color) for field in row])
    table.align = "l"
    print(table)
