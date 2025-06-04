'''
This file contains functions to calculate the following metrics about Python code:
    - Time complexity (based on execution time)
    - Readability (based on cognitive complexity)
'''

from tabulate import tabulate  # Used for nicely formatted table output
import json
import timeit

# ----------------------------- Input Extraction -----------------------------


def extract_input_values(response_json):
    """
    Extracts the input arguments from the test cases in the response JSON.

    Args:
        response_json (dict): A dictionary that contains 'test_inputs' with a list of test case arguments.

    Returns:
        list: A list of input argument tuples (preserving their full structure).
    """
    test_inputs = response_json["test_inputs"]
    n_values = []

    for test_case in test_inputs:
        args = test_case["args"]
        n_values.append((args))  # Preserves the full tuple structure

    print(n_values)
    return n_values


# ----------------------------- Time Complexity -----------------------------


def extract_time_complexity(response_json):
    """
    Extracts the declared time complexity string from a JSON-formatted response.

    Args:
        response_json (str): A JSON-formatted string containing the "time_complexity" key.

    Returns:
        str: The time complexity description (e.g., "O(n log n)") in lowercase.
    """
    str_json = json.loads(response_json)
    time_compl = str_json["time_complexity"]
    return time_compl.lower()


def calculate_time_complexity(code_response_json: str, n_values: list):
    """
    Dynamically executes a provided function and calculates its average execution time
    over a set of input values using the timeit module.

    Args:
        code_response_json (str): A dictionary-like string containing 'imports' and 'code' keys.
        n_values (list): A list of input argument tuples to test the function against.

    Returns:
        float: The average execution time across all input sets.
    """

    # Check for keys and extract the relevant code and imports
    if "imports" and "code" in code_response_json:
        imports = code_response_json["imports"]
        code = code_response_json["code"]

    # Replace escaped newline characters with actual newlines
    code = code.replace("\\n", "\n")

    # Combine the imports and code into one executable string
    str_code = imports + "\n\n" + code

    # Execute the code to define the function and prepare it for testing
    local_ns = {}
    exec(str_code, globals(), local_ns)

    # Automatically detect the function name (assuming there's only one)
    func_name = [name for name in local_ns if callable(local_ns[name])][0]
    func = local_ns[func_name]

    total_times = 0  # Accumulator for total execution time

    # Measure the execution time of the function for each input
    for args in n_values:
        timed_call = lambda: func(*args)
        time = timeit.timeit(timed_call, setup=imports, number=100)
        total_times += time
        print(f'Execution time for {func_name}{args} run 100 times: {time:.6f} s')

    # Compute the average time per input case
    average_time = total_times / len(n_values)
    print(f'\n\nAverage time across {len(n_values)} input values: {average_time :.6f} s')

    return average_time


# ----------------------------- Readability (Cognitive Complexity) -----------------------------

import ast
import astunparse
from inspect import getsource
from cognitive_complexity.api import get_cognitive_complexity_for_node
from cognitive_complexity.utils.ast import is_decorator

def get_cognitive_complexity(func):
    """
    Calculates the cognitive complexity of a Python function, including per-node breakdown.

    Args:
        func (function or str): The function to analyze (can be either a function object or a string of code).

    Returns:
        tuple:
            - int: Total cognitive complexity score of the function.
            - list: Per-node complexity breakdown as [complexity, code snippet].

        Returns (-1, [[-1, <error message>]]) in case of parsing or syntax errors.
    """

    # Convert function to source code if it's a function object
    func = func if isinstance(func, str) else getsource(func)

    try:
        tree = ast.parse(func)  # Parse the code into an AST
    except (SyntaxError, IndentationError) as e:
        return -1, [[-1, f"Syntax error: {e}"]]

    # Get the first FunctionDef node
    funcdef = next((node for node in tree.body if isinstance(node, ast.FunctionDef)), None)
    if funcdef is None:
        return -1, [[-1, "No function definition found"]]

    # Skip decorators if present
    if is_decorator(funcdef):
        return get_cognitive_complexity(funcdef.body[0])

    details = []  # List to hold per-node complexity
    complexity = 0  # Total cognitive complexity

    # Analyze each top-level node in the function body
    for node in funcdef.body:
        node_complexity = get_cognitive_complexity_for_node(node)
        complexity += node_complexity

        node_code = astunparse.unparse(node)

        # Slightly increase complexity if a recursive call is detected
        if f"{funcdef.name}(" in node_code:
            node_complexity += 1
            complexity += 1

        details.append([node_complexity, node_code])

    # Add a final row for the total complexity
    details.append([complexity, "Total"])
    return complexity, details


# ----------------------------- Print Readability Results -----------------------------

def print_cognitive_complexity_details(details_readability_complexity, AGENTS_NO):
    """
    Prints a formatted cognitive complexity breakdown for each agent's function.

    Args:
        details_readability_complexity (list): A list of per-agent complexity details.
        AGENTS_NO (int): Number of agents (functions) analyzed.
    """
    for i in range(AGENTS_NO):
        print("\nCognitive Complexity Details:")
        print(tabulate(details_readability_complexity[i], headers=["Complexity", "Code"], tablefmt="grid"))
