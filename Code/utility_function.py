"""
    Helper functions used in debate strategies.
"""

from metrics import extract_time_complexity
import json

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
