import json
import os
import re
import sys
import subprocess
import yaml
from datetime import datetime
from openai.error import InvalidRequestError
from pprint import pprint
import argparse
from dotenv import load_dotenv
from prettytable import PrettyTable
from termcolor import colored


pg_text_query_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../")
sys.path.append(pg_text_query_path)

from pg_text_query import (
    generate_query,
    describe_database,
)

load_dotenv()

dirname = os.path.dirname(__file__)
test_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(test_dir)


def load_schema(schema_path):
    """
    Loads a JSON schema file and returns its contents.

    Parameters:
        schema_path (str): The path to the schema file.

    Returns:
        dict: The contents of the schema file.
    """
    with open(schema_path) as f:
        schema = json.load(f)
    return schema


def format_sql(sql_code):
    """
    Formats SQL code using the pg_format command-line tool.

    Parameters:
        sql_code (str): The SQL code to format.

    Returns:
        str: The formatted SQL code.
    """
    cmd = ["pg_format", "-s2", "-g", "-n"]
    p = subprocess.Popen(
        cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    stdout, stderr = p.communicate(input=sql_code.encode())
    return stdout.decode().strip()


def get_test_data(category="easy", filename="test_prompts.json"):
    """
    Loads a JSON file containing test prompts and returns the prompts for a specified category.

    Parameters:
        category (str): The category of test prompts to retrieve. Defaults to "easy".
        filename (str): The name of the JSON file containing the test prompts. Defaults to "test_prompts.json".

    Returns:
        list: The test prompts for the specified category.
    """
    prompts_file = os.path.join(root_dir, "test_prompts", filename)
    with open(prompts_file) as f:
        data = json.load(f)
        return data[category]

def load_config(config_file):
    """
    Loads a YAML configuration file and returns its contents.

    Parameters:
        config_file (str): The path to the configuration file.

    Returns:
        dict: The contents of the configuration file.
    """
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    return config


def results_table(results):
    """
    Takes in a dictionary of results containing the user prompt, generated SQL query, 
    expected SQL query, and the result of the query execution, and returns a formatted
    table displaying the results. The table includes the ID, user prompt, generated SQL,
    expected SQL, and the result of the execution.

    Parameters:
    results (dict): A dictionary containing the results of a SQL query execution.

    Returns:
    table (PrettyTable): A formatted table object displaying a summary of the test results
    """
    table = PrettyTable()
    table.field_names = ["ID", "User Prompt", "Generated SQL", "Expected SQL", "Result"]
    for result in results["results"]:
        row = [
            result["id"],
            result["user_prompt"],
            result["sql_output"].strip(),
            result["expected_outputs"],
            colored("SUCCESS", "green")
            if result["success"]
            else colored("FAILURE", "red"),
        ]
        table.add_row(row)
    table._min_width = {"ID": 12, "Result": 14}
    table._max_width = {"User Prompt": 30, "Generated SQL": 55, "Expected SQL": 45}
    table.align = "l"
    table.max_table_width = 120

    table.hrules = True

    return table

def test_prompts(prompt_template, test_case_file, category="easy",
                 verbose=False, type="single", model_params: dict={}):
    """
    Executes SQL query test cases using the provided prompt template and test data.
    The function generates SQL queries using the prompt template and compares the
    results to the expected outputs provided in the test data.

    Parameters:
    prompt_template (str): A string representing a SQL prompt template.
    test_case_file (str): The name of the test case file to use.
    category (str): The difficulty category of the test cases. Default is "easy".
    verbose (bool): A flag indicating whether to print the log results. Default is False.
    type (str): The type of completion method to use. Default is "single".
    model_params (dict): A dictionary containing additional model parameters for
    generating SQL queries. Default is an empty dictionary.

    Returns:
    log_results (dict): A dictionary containing the log results of the test cases.
    The dictionary includes the task prompt, model parameters, test results, total
    number of test cases, and number of successful test cases.
    """
     
    log_results = {"task_prompt": prompt_template,
                   "model_params":model_params,
                   "results": []}

    counter = 0
    n_success = 0
    
    for test_case in get_test_data(category, test_case_file):
        id = test_case["id"]
        user_prompt = test_case["prompt"]
        expected_outputs = test_case["expected_outputs"]
        schema = test_case["schema"]

        schema_path = os.path.join(root_dir, "test_prompts", "test_schemas", schema)
        db_schema = load_schema(schema_path)
        prompt = prompt_template.format(schema=describe_database(db_schema), user_prompt=user_prompt)

        
        try:
            sql_output = generate_query(prompt, completion_type=type, **model_params)
        except InvalidRequestError as e:
            raise e
           
        assert sql_output is not None, f"Generated SQL code is None: prompt={prompt}"

        success = False
        for expected_output in expected_outputs:
            escaped_output = re.escape(format_sql(expected_output)).rstrip(";")
            regex_pattern = f"^{escaped_output}(?=;)?"
            if re.match(regex_pattern, format_sql(sql_output).strip(), re.IGNORECASE):
                success = True
                break
        
        if success:
            n_success += 1
            counter += 1
        else:
            counter += 1

        result = {
            "id": id,
            "user_prompt": user_prompt,
            "task_prompt": prompt_template,
            "prompt": prompt,
            "expected_outputs": expected_outputs,
            "sql_output": sql_output,
            "success": success,
        }

        log_results["results"].append(result)
        
    log_results.update({"total": counter, "successful": n_success})
    if verbose:
        pprint(log_results)
    return log_results



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Text to SQL Translation Test Suite")

    parser.add_argument(
        "--config-file",
        "-c",
        dest="config_file",
        type=str,
        default=None,
        help="the YAML configuration for the test. See config_template.yaml"
    )

    parser.add_argument(
        "--log-file",
        "-l",
        dest="log_file",
        type=str,
        default=None,
        help="Destination for test logs. New logs will be appended if the file already exists."
    )
    
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        dest="verbose",
        help="whether to print log output to terminal")

    args = parser.parse_args()
    config = load_config(args.config_file)
    prompt_template = config.get("prompt", {}).get("template",
                    "A PostgreSQL Query to SELECT 1 and a PostgreSQL query to {user_prompt}")
    category = config.get("test_cases", {}).get("category", "one_test")
    filename = config.get("test_cases", {}).get("filename", "test_prompts.json")
    log_file = config.get("log", {}).get("path", None)
    model_type = config.get("model", {}).get("type", "chat")
    model_params = config.get("model", {}).get("params", {})

    results = test_prompts(
        prompt_template=prompt_template,
        test_case_file=filename,
        category=category,
        verbose=args.verbose,
        type=model_type,
        model_params = model_params,
    )

    results.update({
        "test_name": config.get("test_name", "unnamed"),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "config_file": args.config_file,
    })

    print(results_table(results))
    # Update the log file with the new results
    
    if args.log_file:
        # Create a unique key using the test name and timestamp
        test_key = f"{results['test_name']}_{results['timestamp'].replace(' ', '_')}"

        # Open the log file and load existing data if it exists
        try:
            with open(args.log_file, "r") as f:
                log_data = json.load(f)
        except (FileNotFoundError, json.decoder.JSONDecodeError):
            log_data = []

        # Append the data to the log and write to file
        data={test_key: results}
        log_data.append(data)
        with open(args.log_file, "w") as f:
            json.dump(log_data, f, indent=4)
