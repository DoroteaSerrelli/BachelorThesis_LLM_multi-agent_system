''' This file contains functions to calculate the following metrics about code:
    - time complexity
    - readability
'''

from tabulate import tabulate


def extract_input_values(response_json):
    test_inputs = response_json["test_inputs"]
    n_values = []

    for test_case in test_inputs:
        args = test_case["args"]
        n_values.append((args))  # Preserve full structure

    print(n_values)
    return n_values

import json

def extract_time_complexity(response_json):
    str_json = json.loads(response_json)
    print("In extract_time_complexity si è ricevuto un oggetto di tipo: " + str(type(str_json)))
    print("Risposta ricevuta: " + str(str_json))
    time_compl = str_json["time_complexity"]

    return time_compl.lower()


'''
    Time complexity (used in main_test_inputs.py)
    
    This script estimates the average time complexity of a Python function by measuring its execution 
    time over a range of input sizes, using the timeit module.
    
'''
import timeit

def calulate_time_complexity(code_response_json: str, n_values: list):
    """
    Calculates the average time complexity (i.e., average execution time) of a function
    provided as a string of code.

    Args:
        code_response_json (str): A dictionary-like string (should contain 'imports' and 'code') with the necessary imports and function definition.
        n_values (list): A list of input values to test the function with.

    Returns:
        float: The average execution time of the function across all input sizes.
    """

    # Extract the imports and code from the response
    if "imports" and "code" in code_response_json:
        imports = code_response_json["imports"]
        code = code_response_json["code"]

    # Replace the '\\n' sequences with real newlines '\n'
    code = code.replace("\\n", "\n")

    str_code = imports + "\n\n" + code # Code to execute

    # Dynamically execute the code string, defining the function and any required imports
    local_ns = {}
    exec(str_code, globals(), local_ns)

    func_name = [name for name in local_ns if callable(local_ns[name])][0]
    func = local_ns[func_name]

    # Accumulates the total execution time across all input values
    total_times = 0

    # Iterate through each input size and measure how long the function takes to run
    for args in n_values:
        timed_call = lambda: func(*args)
        # Measure execution time over n iterations
        time = timeit.timeit(timed_call, setup=imports, number=100)
        total_times += time
        print(f'Execution time for {func_name}{args} run 100 times: {time:.6f} s')

    # Calculate and return the average time
    average_time = total_times / len(n_values)
    print(f'\n\nAverage time across {len(n_values)} input values: {average_time :.6f} s')

    return average_time



'''
    Readability
    This script calculates the cognitive complexity of a Python function.
    Cognitive complexity is a metric that reflects how difficult code is to understand,
    based on factors like nesting, conditionals, recursion, and control flow.
'''

import ast
import astunparse
from inspect import getsource
from cognitive_complexity.api import get_cognitive_complexity_for_node
from cognitive_complexity.utils.ast import is_decorator


def get_cognitive_complexity(func):
    """
        Calculates the cognitive complexity of a Python function, including per-node details.

        Args:
            func (function or str): The function to analyze (can be a function object or a string of code).

        Returns:

            tuple:
                - complexity (int): The total cognitive complexity score.
                - details (list): A list of [node_complexity, node_code] pairs for each top-level statement.

        Returns (-1, []) in case of syntax or parsing errors.
    """

    """
    Calculates the cognitive complexity of a Python function, including per-node details.
    
    """

    func = func if isinstance(func, str) else getsource(func)

    try:
        tree = ast.parse(func)
    except (SyntaxError, IndentationError) as e:
        return -1, [[-1, f"Syntax error: {e}"]]

    funcdef = next((node for node in tree.body if isinstance(node, ast.FunctionDef)), None)
    if funcdef is None:
        return -1, [[-1, "No function definition found"]]

    if is_decorator(funcdef):
        return get_cognitive_complexity(funcdef.body[0])

    details = []
    complexity = 0
    for node in funcdef.body:
        node_complexity = get_cognitive_complexity_for_node(node)
        complexity += node_complexity
        node_code = astunparse.unparse(node)
        if f"{funcdef.name}(" in node_code:
            node_complexity += 1
            complexity += 1
        details.append([node_complexity, node_code])

    details.append([complexity, "Total"])
    return complexity, details


''' Print details related to cognitive complexity per-node'''

def print_cognitive_complexity_details(details_readability_complexity, AGENTS_NO):
    for i in range(0, AGENTS_NO):
        # Stampa in formato tabellare
        print("\nDettagli della complessità:")
        print(tabulate(details_readability_complexity[i], headers=["Complexity", "Code"], tablefmt="grid"))
