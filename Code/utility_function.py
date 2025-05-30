"""
    Helper functions used in debate strategies.
"""

from metrics import extract_time_complexity
import json

def extract_documentation(response_json):
        str_json = json.loads(response_json)
        docs = str_json["documentation"]

        return docs

def get_set_number_solutions(placeholder, AGENTS_NO):
    """
        Returns a list of agent indices excluding the one specified by `placeholder`.

        Parameters:
        - placeholder (int): Index of the agent to exclude.
        - AGENTS_NO (int): Total number of agents.

        Used to identify all other agents except the current one, useful for peer evaluation.
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
        Removes duplicate elements from a list while preserving order.

        Parameters:
        - list_local (List): List containing potential duplicates.

        Returns:
        - List with unique elements in the original order of appearance.
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
        Checks whether all given solutions have the same time complexity.

        Parameters:
        - solutions (List[str]): List of solution code snippets or descriptors.

        Returns:
        - True if all time complexities are identical, False otherwise.

        Internally uses `extract_time_complexity()` to analyze each solution.
    """

    list_local = []
    for var in solutions:
        list_local.append(extract_time_complexity(var))
    print("Complessità di tempo estratte: ")
    print(list_local)
    set_local = set(list_local)
    if len(set_local) == 1:
        return True
    else:
        return False


def equals_cognitive_complexity(k_cognitive_complexity_sol):
    """
        Checks if all cognitive complexity scores are equal across solutions.

        Parameters:
        - cognitive_complexity_sol: dict.

        Returns:
        - True if all scores are the same, False otherwise.
    """

    set_local = set(k_cognitive_complexity_sol.values())
    if len(set_local) == 1:
        return True
    else:
        return False


def get_random_element(list_local):
    """
        Randomly selects and returns an element from a list.

        Parameters:
        - list_local (List): List of items to choose from.

        Returns:
        - A randomly selected element, or None if the list is empty.

        Useful when multiple equally valid solutions exist and a tie-breaker is needed.
    """
    import random

    if not list_local:
        return None
    return random.choice(list_local)


def get_k_responses(response, feedback):
    k_responses = []

    for i in feedback:
        k_responses.append(response[int(i)])

    return k_responses

# Convert JSON schema response into a code response: imports+code

def get_formatted_code_solution(ai_response):

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
    Extracts the value of "response" from a JSON object conforming to schema_feedback.

    Args:
        json_data (str or dict): The JSON string or Python dictionary to extract from.

    Returns:
        int: The integer value associated with the "response" key.
        None: If the JSON is invalid or the "response" key is not present
              (even though the schema makes it required, this helps with robustness).
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



# Token counts
from transformers import AutoTokenizer

# Usa il tokenizer adatto al tuo modello
tokenizer = AutoTokenizer.from_pretrained("codellama/CodeLlama-13b-Instruct-hf")

def count_tokens(text):
    return len(tokenizer.tokenize(text))

# FUNZIONE PER AUTOMATIZZARE LA COMPILAZIONE DI CODE SNIPPET

import tempfile
import os
import py_compile
import subprocess
import sys

def save_and_test_code(full_code_str):
    """
    Salva la stringa di codice completa in un file temporaneo,
    compila e esegue il codice Python,
    stampa output o errori.
    """
    # Crea file temporaneo
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as tmp_file:
        tmp_file.write(full_code_str)
        tmp_filepath = tmp_file.name

    print(f"\n[INFO] Codice salvato in file temporaneo: {tmp_filepath}")

    # Prova a compilare
    try:
        py_compile.compile(tmp_filepath, doraise=True)
        print(f"✓ Byte-code generato per {os.path.basename(tmp_filepath)}")
    except py_compile.PyCompileError as err:
        print("🛑 SYNTAX ERROR durante la compilazione:\n")
        print(err.msg)
        return

    # Esegui il file in subprocess
    completed = subprocess.run(
        [sys.executable, tmp_filepath],
        text=True,
        capture_output=True
    )

    if completed.returncode == 0:
        print("\n💬 OUTPUT PROGRAMMA ↓↓↓\n")
        print(completed.stdout)
    else:
        print("\n🔥 ECCEZIONE RUNTIME ↓↓↓\n")
        print(completed.stderr)

    # Elimina il file temporaneo (<=== DA VEDERE)
    # os.unlink(tmp_filepath)


# FUNZIONE PER AUTOMATIZZARE L'ESECUZIONE DI TEST UNITARI
'''
import subprocess
import tempfile
import os
import shutil

def evaluate_code_with_tests(code: str, test_code: str) -> bool:
    """Valuta se il codice dell'agente passa tutti i test di BigCodeBench."""
    print("[*] Inizio valutazione codice con test...")
    temp_dir = tempfile.mkdtemp(prefix="agent_eval_")
    print(f"[*] Cartella temporanea creata: {temp_dir}")
    passed = False

    try:
        # Scrivi la soluzione dell'agente in submission.py
        submission_path = os.path.join(temp_dir, "submission.py")
        with open(submission_path, "w") as f:
            f.write(code)
        print(f"[*] Codice scritto in {submission_path}")

        # Scrivi i test in test_case.py
        test_with_import = "from submission import task_func\n" + test_code
        test_path = os.path.join(temp_dir, "test_case.py")
        with open(test_path, "w") as f:
            f.write(test_with_import)
        print(f"[*] Test scritto in {test_path}")

        # Esegui i test con unittest
        print("[*] Esecuzione test con unittest...")
        result = subprocess.run(
            ["python3", "-m", "unittest", "test_case.py"],
            cwd=temp_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10
        )
        print("[*] Test eseguiti.")

        passed = result.returncode == 0
        if passed:
            print("[✅] Tutti i test sono passati.")
        else:
            print("[❌] Test falliti:")
            print(result.stdout.decode())
            print(result.stderr.decode())

    except subprocess.TimeoutExpired:
        print("[!] Timeout nei test")
        passed = False

    except Exception as e:
        print(f"[!] Errore durante l'esecuzione dei test: {e}")
        passed = False

    finally:
        shutil.rmtree(temp_dir)
        print(f"[*] Cartella temporanea {temp_dir} rimossa.")

    return passed
'''

import subprocess
import tempfile
import os
import shutil
import re


def evaluate_code_with_tests(code: str, test_code: str) -> dict:
    """Valuta se il codice dell'agente passa tutti i test e conta successi e fallimenti."""
    print("[*] Inizio valutazione codice con test...")
    temp_dir = tempfile.mkdtemp(prefix="agent_eval_")
    print(f"[*] Cartella temporanea creata: {temp_dir}")

    passed = False
    tests_run = 0
    tests_failed = 0

    try:
        # Scrivi la soluzione dell'agente in submission.py
        submission_path = os.path.join(temp_dir, "submission.py")
        with open(submission_path, "w") as f:
            f.write(code)
        print(f"[*] Codice scritto in {submission_path}")

        # Scrivi i test in test_case.py
        test_with_import = "from submission import task_func\n" + test_code
        test_path = os.path.join(temp_dir, "test_case.py")
        with open(test_path, "w") as f:
            f.write(test_with_import)
        print(f"[*] Test scritto in {test_path}")

        # Esegui i test con unittest
        print("[*] Esecuzione test con unittest...")
        result = subprocess.run(
            ["python3", "-m", "unittest", "test_case.py"],
            cwd=temp_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10
        )
        print("[*] Test eseguiti.")

        output = result.stdout.decode() + result.stderr.decode()
        # Estrarre il numero di test eseguiti (es: Ran 3 tests in ...)
        match_run = re.search(r"Ran (\d+) tests?", output)
        if match_run:
            tests_run = int(match_run.group(1))

        # Estrarre fallimenti/ errori (es: FAILED (failures=1, errors=0))
        match_failed = re.search(r"FAILED \(failures=(\d+)(?:, errors=(\d+))?", output)
        if match_failed:
            failures = int(match_failed.group(1))
            errors = int(match_failed.group(2)) if match_failed.group(2) else 0
            tests_failed = failures + errors
        else:
            # Se non è presente FAILED, assumiamo 0 fallimenti
            tests_failed = 0

        tests_passed = tests_run - tests_failed
        passed = tests_failed == 0

        if passed:
            print(f"[✅] Tutti i test sono passati ({tests_passed}/{tests_run}).")
        else:
            print(f"[❌] Test falliti: {tests_failed} su {tests_run}")
            print(output)

    except subprocess.TimeoutExpired:
        print("[!] Timeout nei test")
        passed = False

    except Exception as e:
        print(f"[!] Errore durante l'esecuzione dei test: {e}")
        passed = False

    finally:
        shutil.rmtree(temp_dir)
        print(f"[*] Cartella temporanea {temp_dir} rimossa.")

    return {
        "passed": passed,
        "tests_run": tests_run,
        "tests_passed": tests_passed if 'tests_passed' in locals() else 0,
        "tests_failed": tests_failed if 'tests_failed' in locals() else 0
    }

# FUNZIONE PER SALVARE I RISULTATI IN UN FILE CSV

import csv
import os


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
        tests_success,
        test_fails
):
    # Controlla se il file esiste già
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
            'evaluation',
            'tests_success',
            'test_fails'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        # Scrivi intestazione solo se il file non esiste
        if not file_exists:
            writer.writeheader()

        # Scrivi la riga di dati
        writer.writerow({
            'task_id': task_id,
            'instruct_prompt': instruct_prompt,
            'canonical_solution': canonical_solution,
            'code_multiagent_system': code_multiagent_system,
            'documentation': documentation,
            'cognitive_complexity': cognitive_complexity,
            'time_complexity': time_complexity,
            'evaluation': evaluation,
            'tests_success': tests_success,
            'test_fails': test_fails
        })

# FUNZIONE PER INTEGRAZIONE DI SONARQUBE PER CALCOLO COGNITIVE COMPLEXITY, SICUREZZA, AFFIDABILITA' E MANUTANIBILITA'

import os
import json
import uuid
import csv
import requests
import subprocess
import shutil

# === CONFIGURAZIONE ===
SONAR_HOST = "http://localhost:9000"
SONAR_TOKEN = "YOUR_SONAR_TOKEN"
SONAR_SCANNER_CMD = "sonar-scanner"

# === CREA TEMP DIR + ANALIZZA CODICE CON SONARQUBE ===
def analyze_code_sonarqube(code: str) -> tuple[str, int]:
    project_key = f"multiagent-{uuid.uuid4().hex[:8]}"
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
        print(f"[!] Errore analisi Sonar: {e}")
        return project_key, -1

    complexity = get_cognitive_complexity_sonarqube(project_key)
    return project_key, complexity

# === RECUPERA COGNITIVE COMPLEXITY VIA API ===
def get_cognitive_complexity_sonarqube(project_key: str) -> int:
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