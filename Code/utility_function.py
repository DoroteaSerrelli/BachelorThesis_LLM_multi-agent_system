"""
    Helper functions used in debate strategies for multi-agent evaluation systems.
"""

from metrics import extract_time_complexity
import json


def extract_documentation(response_json):
    """
        Extracts the 'documentation' field from a JSON string response.

        Parameters:
        - response_json (str): A JSON-formatted string containing a 'documentation' key.

        Returns:
        - The content of the 'documentation' key.
    """
    str_json = json.loads(response_json)
    docs = str_json["documentation"]

    return docs


def get_set_number_solutions(placeholder, AGENTS_NO):
    """
        Returns a list of agent indices excluding the one specified by `placeholder`.

        Parameters:
        - placeholder (int): The index of the agent to exclude.
        - AGENTS_NO (int): Total number of agents.

        Returns:
        - A list of agent indices excluding the one specified.

        Useful for peer comparison or voting among agents.
    """

    list_local = [None] * AGENTS_NO

    for i in range(0, AGENTS_NO):
        list_local[i] = i

    for var in list_local:
        if var == int(placeholder):
            list_local.remove(var)
            break

    return list_local


def remove_duplicates(list_local):
    """
        Removes duplicates from a list while preserving the original order.

        Parameters:
        - list_local (list): Input list that may contain duplicates.

        Returns:
        - List with unique elements in the same order as their first occurrence.
    """

    result = []
    explored = set()
    for element in list_local:
        if element not in explored:
            result.append(element)
            explored.add(element)
    return result


def equals_time_complexity(solutions):
    """
        Checks whether all solutions share the same time complexity.

        Parameters:
        - solutions (list of str): A list of code snippets or solution descriptions.

        Returns:
        - True if all solutions have the same time complexity, False otherwise.
    """

    list_local = []
    for var in solutions:
        list_local.append(extract_time_complexity(var))
    print("Extracted time complexities: ")
    print(list_local)
    set_local = set(list_local)
    if len(set_local) == 1:
        return True
    else:
        return False


def equals_cognitive_complexity(k_cognitive_complexity_sol):
    """
        Verifies if all cognitive complexity scores are equal.

        Parameters:
        - k_cognitive_complexity_sol (dict): Dictionary of scores (e.g., from agents).

        Returns:
        - True if all values are the same, False otherwise.
    """

    set_local = set(k_cognitive_complexity_sol.values())
    if len(set_local) == 1:
        return True
    else:
        return False


def get_random_element(list_local):
    """
        Randomly selects one element from a non-empty list.

        Parameters:
        - list_local (list): List to pick from.

        Returns:
        - A randomly selected element or None if the list is empty.
    """

    import random

    if not list_local:
        return None
    return random.choice(list_local)


def get_k_responses(response, feedback):
    """
        Retrieves specific elements from the response list based on feedback indices.

        Parameters:
        - response (list): List of agent responses.
        - feedback (list): List of indices indicating which responses to return.

        Returns:
        - A list of selected responses.
    """

    k_responses = []

    for i in feedback:
        print("GET K RESPONSES: " + str(i))
        k_responses.append(response[int(i)])

    return k_responses


def get_formatted_code_solution(ai_response):
    """
        Formats a code response from a JSON schema containing 'imports' and 'code'.

        Parameters:
        - ai_response (str): JSON string with fields 'imports' and 'code'.

        Returns:
        - A single string combining imports and code, or None if fields are missing.
    """
    response_json = json.loads(ai_response)
    if "imports" in response_json and "code" in response_json:
        imports = response_json["imports"]
        code = response_json["code"]
        if imports != "":
            return f"{imports}\n\n{code}"
        else:
            return f"{code}"
    else:
        return None


def get_feedback_value(json_data):
    """
        Extracts the 'response' integer value from a JSON input.

        Parameters:
        - json_data (str or dict): JSON string or parsed dictionary.

        Returns:
        - Integer value from the 'response' key, or None if not valid or missing.
        """
    if isinstance(json_data, str):
        try:
            data = json.loads(json_data)
        except json.JSONDecodeError:
            print("Error: The provided string is not valid JSON.")
            return None
    elif isinstance(json_data, dict):
        data = json_data
    else:
        print("Error: Input must be a JSON string or a dictionary.")
        return None

    if "response" in data and isinstance(data["response"], int):
        print("HO OTTENUTO " + str(data["response"]))
        return data["response"]
    else:
        print("Error: The 'response' key not found or is not an integer.")
        return None


# === COMPILE & RUN CODE IN TEMP FILE ===

import tempfile
import os
import py_compile
import subprocess
import sys


def save_and_test_code(full_code_str):
    """
        Saves the provided Python code to a temp file, compiles it, and executes it.

        Parameters:
        - full_code_str (str): Complete Python code to compile and run.

        Prints:
        - Compilation success or syntax error.
        - Runtime output or exception traceback.
    """

    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as tmp_file:
        tmp_file.write(full_code_str)
        tmp_filepath = tmp_file.name

    print(f"\n[INFO] Code saved to temporary file: {tmp_filepath}")

    # Prova a compilare
    try:
        py_compile.compile(tmp_filepath, doraise=True)
        print(f"✓ Byte-code successfully generated for {os.path.basename(tmp_filepath)}")
    except py_compile.PyCompileError as err:
        print("🛑 SYNTAX ERROR during compilation:\n")
        print(err.msg)
        return

    # Execute the file in subprocess
    completed = subprocess.run(
        [sys.executable, tmp_filepath],
        text=True,
        capture_output=True
    )

    if completed.returncode == 0:
        print("\n💬 PROGRAM OUTPUT ↓↓↓\n")
        print(completed.stdout)
    else:
        print("\n🔥 RUNTIME EXCEPTION ↓↓↓\n")
        print(completed.stderr)

    # Delete temporary file
    os.unlink(tmp_filepath)

import os
import tempfile
import subprocess
import sys
import shutil
import re

# === UNIT TEST EXECUTION & REPORTING ===


def evaluate_code_with_tests(code: str, test_code: str) -> dict:
    """
        Compiles and runs a given Python solution with its unittest-based test suite.

        Parameters:
        - code (str): The user’s submitted code.
        - test_code (str): Test suite code in unittest format.

        Returns:
        - Dictionary with test results:
            - passed: True if all tests passed.
            - tests_run: Number of tests executed.
            - tests_passed: Number of successful tests.
            - tests_failed: Number of failed or errored tests.
    """
    print("[*] Starting code evaluation with tests...")
    temp_dir = tempfile.mkdtemp(prefix="agent_eval_")
    print(f"[*] Temporary folder created: {temp_dir}")

    passed = False
    tests_run = 0
    tests_failed = 0
    tests_passed = 0
    output = ""

    try:
        submission_path = os.path.join(temp_dir, "submission.py")
        with open(submission_path, "w", encoding="utf-8") as f:
            f.write(code)

        test_path = os.path.join(temp_dir, "test_case.py")
        with open(test_path, "w", encoding="utf-8") as f:
            f.write("from submission import task_func\n" + test_code)

        result = subprocess.run(
            [sys.executable, "-m", "unittest", "test_case"],
            cwd=temp_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10
        )

        output = result.stdout.decode() + result.stderr.decode()
        print("OUTPUT TESTS\n\n---" + output)

    except subprocess.TimeoutExpired:
        output += "\n[!] Test execution timed out."
        print(output)
    except Exception as e:
        output += f"\n[!] Exception occurred during testing: {e}"
        print(output)
    finally:
        match_run = re.search(r"Ran (\d+) tests?", output)
        if match_run:
            tests_run = int(match_run.group(1))

        match_failed = re.search(r"FAILED \(failures=(\d+)(?:, errors=(\d+))?", output)
        if match_failed:
            failures = int(match_failed.group(1))
            errors = int(match_failed.group(2)) if match_failed.group(2) else 0
            tests_failed = failures + errors
        else:
            match_errors = re.search(r"FAILED \(errors=(\d+)\)", output)
            if match_errors:
                tests_failed = int(match_errors.group(1))

        tests_passed = tests_run - tests_failed
        passed = tests_failed == 0

        shutil.rmtree(temp_dir)
        print(f"[✔️] Tests run: {tests_run}, Passed: {tests_passed}, Failed: {tests_failed}")

    return {
        "passed": passed,
        "tests_run": tests_run,
        "tests_passed": tests_passed,
        "tests_failed": tests_failed
    }


# === CSV LOGGING FOR EXPERIMENT RESULTS ===

def save_task_data_to_csv(
        filepath: str,
        task_id,
        instruct_prompt,
        canonical_solution,
        code_multiagent_system,
        documentation,
        cognitive_complexity,
        time_complexity,
        evaluation,
        metrics_sonarqube,
        no_agents,
        type_models,
        max_rounds,
        time,
        debate_strategy,
        tests_success,
        test_fails
):
    """
        Appends experiment data to a CSV file for analysis and tracking.

        Creates the file with headers if it does not already exist.

        Parameters:
        - filepath (str): CSV file path to write to.
        - All other parameters represent recorded metrics for a test run.
        """

    # Check if the file exists
    file_exists = os.path.isfile(filepath)

    with open(filepath, mode='a', newline='', encoding='utf-8') as csvfile:
        fieldnames = [
            'task_id',
            'instruct_prompt',
            'canonical_solution',
            'code_multiagent_system',
            'documentation',
            'cognitive_complexity',
            'time_complexity',
            'evaluation_feedback',
            'number_agents',
            'metrics_sonarqube',
            'type_models',
            'max_rounds',
            'time',
            'debate_strategy',
            'tests_success',
            'test_fails'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        # Write fields only if the file doesn't exist
        if not file_exists:
            writer.writeheader()

        # Write data
        writer.writerow({
            'task_id': task_id,
            'instruct_prompt': instruct_prompt,
            'canonical_solution': canonical_solution,
            'code_multiagent_system': code_multiagent_system,
            'documentation': documentation,
            'cognitive_complexity': cognitive_complexity,
            'time_complexity': time_complexity,
            'evaluation_feedback': evaluation,
            'metrics_sonarqube': metrics_sonarqube,
            'number_agents': no_agents,
            'type_models': type_models,
            'max_rounds': max_rounds,
            'time': time,
            'debate_strategy': debate_strategy,
            'tests_success': tests_success,
            'test_fails': test_fails
        })


# === SONARQUBE INTEGRATION FOR CODE QUALITY ANALYSIS ===

import os
import json
import uuid
import csv
import requests
import subprocess
import shutil

# === CONFIGURAZIONE ===
SONAR_HOST = "http://localhost:9000"
SONAR_TOKEN = "MY_TOKEN"
SONAR_SCANNER_CMD = "C:\\sonar-scanner-7.1.0.4889-windows-x64\\bin\\sonar-scanner.bat"
project_key = "MY_PROJECT_KEY"


def analyze_code_sonarqube(code: str) -> tuple[str, dict]:
    """
        Analyzes the given code using SonarQube and retrieves its metrics.

        Parameters:
        - code (str): Python source code to analyze.

        Returns:
        - Tuple containing the project key and a dictionary of SonarQube metrics.
        """
    #project_key = f"multiagent-{uuid.uuid4().hex[:8]}"
    tmp_dir = f"./temp_sonar_{uuid.uuid4().hex[:6]}"
    os.makedirs(tmp_dir, exist_ok=True)

    # Salva codice
    code_path = os.path.join(tmp_dir, "solution.py")
    with open(code_path, "w") as f:
        f.write(code)

    # Configurazione sonar
    with open(os.path.join(tmp_dir, "sonar-project.properties"), "w") as f:
        f.write(f"""
sonar.projectKey={project_key}
sonar.sources=.
sonar.host.url={SONAR_HOST}
sonar.login={SONAR_TOKEN}
        """)

    try:
        subprocess.run([SONAR_SCANNER_CMD], cwd=tmp_dir, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        print(f"[!] Sonar analysis failed: {e}")
        return project_key, -1

    other_measures = get_all_sonar_metrics(project_key)
    return project_key, other_measures


def get_cognitive_complexity_sonarqube(project_key: str) -> int:
    """
        Retrieves cognitive complexity metric for the given project from SonarQube.

        Parameters:
        - project_key (str): SonarQube project identifier.

        Returns:
        - Cognitive complexity score as integer, or -1 on failure.
        """
    url = f"{SONAR_HOST}/api/measures/component"
    params = {
        "component": project_key,
        "metricKeys": "cognitive_complexity"
    }
    auth = (SONAR_TOKEN, "")
    try:
        r = requests.get(url, params=params, auth=auth)
        data = r.json()
        return int(data["component"]["measures"][0]["value"])
    except Exception as e:
        print(f"[!] Errore API SonarQube: {e}")
        return -1


def get_all_sonar_metrics(project_key: str) -> dict:
    """
        Retrieves a set of code quality metrics from SonarQube for the given project.

        Parameters:
        - project_key (str): Identifier of the analyzed project in SonarQube.

        Returns:
        - Dictionary of metrics such as cognitive complexity, reliability, maintainability, etc.
        """

    url = f"{SONAR_HOST}/api/measures/component"
    metric_keys = ",".join([
        "cognitive_complexity",
        "security_rating",
        "reliability_rating",
        "sqale_rating",  # maintainability rating
        "bugs",
        "vulnerabilities",
        "code_smells",
        "coverage",
        "duplicated_lines_density",
        "ncloc"
    ])
    params = {
        "component": project_key,
        "metricKeys": metric_keys
    }
    auth = (SONAR_TOKEN, "")
    try:
        r = requests.get(url, params=params, auth=auth)
        r.raise_for_status()
        data = r.json()

        metrics = {}
        for measure in data.get("component", {}).get("measures", []):
            metrics[measure["metric"]] = measure["value"]

        return metrics
    except Exception as e:
        print(f"[!] SonarQube metrics fetch failed: {e}")
        return {}