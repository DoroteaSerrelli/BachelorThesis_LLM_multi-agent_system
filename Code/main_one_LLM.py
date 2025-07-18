"""
    LLM-Based Code Generation and Evaluation Pipeline

    This script implements a single-agent system using a large language model (LLM)
    designed to generate source code in response to user prompts. The generated code
    is evaluated by an automated evaluator, which assigns feedback and a numerical score
    based on predefined quality criteria (e.g., correctness, time complexity, cognitive complexity).

    If the evaluation score falls below a threshold, the agent engages in a self-refinement
    process, revising its previous solution using the evaluator's feedback in a structured manner.

    Purpose:
    This implementation is part of an experimental framework to compare the performance of:
    - A single LLM with high parameter count (monolithic model)
    - A multi-agent LLM-based system (collaborative/refinement-based)

    The output quality, number of refinement rounds, and evaluation metrics from this script
    will serve as a baseline for performance comparison.
"""

# === IMPORTS ===

# LLM configuration (using LMStudio or compatible backend)
import lmstudio as lms

# Code quality metrics
from Code.metrics import get_cognitive_complexity, extract_time_complexity

# Set up the local inference server for LMStudio
SERVER_API_HOST = "localhost:1234"  #server lmstudio port <--- 2345
lms.configure_default_client(SERVER_API_HOST)

# Benchmark data from BigCodeBench (prompts, canonical solutions, tests, etc.)
from evaluation_bigcodebench import instruct_prompt_list, canonical_solution_list, test_list, libs_list

# Import the function to get the first response from the LLM
from LLM_definition import get_programmer_first_response

# Import schema used to enforce structure of complex JSON responses
from response_JSON_schema import schema_complexity

# Import constants and utility functions for managing multi-round debates

from LLM_definition import get_clone_agent
from utility_function import get_formatted_code_solution, save_and_test_code, evaluate_code_with_tests, \
    extract_documentation, save_task_data_to_csv, analyze_code_sonarqube
from evaluator import eval_code, get_evaluator, extract_criteria_scores, calculate_score_code, extract_explanation

import time

# Maximum number of refinement response rounds allowed based on evaluator feedback, before ending the debate
# with a partial solution.
MAX_EVAL_ROUNDS = 4


# === FUNCTION DEFINITIONS ===

def get_response_unique(model, user_prompt):
    """
        Sends a single prompt to the LLM and requests a structured JSON response conforming to schema_complexity.
    """

    messages = [{"role": "user", "content": user_prompt}]
    response = model.respond({"messages": messages}, response_format=schema_complexity)
    return response.content


def self_refinement_unique(user_prompt, feedback_evaluator, previous_code):
    """
        Constructs a refinement prompt using previous code, evaluator feedback, and the original prompt.
        Requests the LLM to return a revised version of the code in JSON format.
        """

    refinement_instruction_prompt = \
        '''# Instruction
            Your task is to refine the previous solution to the code generation task based on the feedback provided by the evaluator.
            We will provide you with the user input (the original coding prompt), an AI-generated code response and a feedback by the evaluator.
            Carefully analyze the feedback and revise the previous AI-generated code to address the identified issues and
            improve its overall quality according to the evaluation criteria.

            #User prompt
            {user_prompt}

            # Previous source code
            {previous_code}

            # Evaluation Feedback
            {evaluation_feedback}

            # Refinement Guidelines
            Based on the feedback, focus on the following aspects:
            -   *Correctness*: Ensure the refined code fully satisfies the requirements outlined in the original user prompt. Specifically address the reasoning behind the correctness score given in the feedback and make necessary modifications to ensure the code functions as intended.
            -   *Time Complexity*: The time complexity of the refined code, expressed in Big-O notation, must not be worse than the time complexity of the previous code. Strive to maintain or even improve the efficiency of the algorithm. Clearly state the time complexity of your refined code.
            -   *Cognitive Complexity*: The cognitive complexity of the refined code must equal or lower than the cognitive complexity of the previous code. Simplify the logic and structure of the code to enhance its readability and maintainability, without compromising correctness or time complexity.

            # Output Format
            Provide the refined source code in the following JSON format:

            {
                "type": "object",
                "properties": {
                    "documentation": {
                        "type": "string",
                        "description": "Description of the problem and approach"
                    },
                    "imports": {
                        "type": "string",
                        "description": "Code block import statements"
                    },
                    "code": {
                        "type": "string",
                        "description": "Code block not including import statements"
                    },
                    "time_complexity": {
                        "type": "string",
                        "description": "Time complexity of the code block not including import statements, expressed in Big-O notation"
                    }
                },
                "required": ["documentation", "imports", "code", "time_complexity"]
            }


            which includes:
            - The code block import statements 
            - The code
            - A description explaining the code (documentation)
            - The time complexity of the code block not including import statements, expressed in Big-O notation

            Output ONLY the JSON object. Do not include any extra text outside the JSON block.'''

    # Fill in the placeholders in the instruction with actual input values
    refinement_prompt = refinement_instruction_prompt.replace("{user_prompt}", user_prompt)
    refinement_prompt = refinement_prompt.replace("{previous_code}", previous_code)
    refinement_prompt = refinement_prompt.replace("{evaluation_feedback}", feedback_evaluator)

    # Generate a refined solution using the model
    refined_solution = get_response_unique(agent, refinement_prompt)
    return refined_solution


# ================ MAIN ================#

# Few-shot prompt to guide the LLM agents on how to structure their responses in JSON format
# It includes multiple examples of correct outputs for different types of coding tasks

role_programmer_prompt = """You are an AI expert programmer that writes code or helps to review code for bugs,
based on the user request. Given the user prompt, inserted in **CODE GENERATION TASK** section, provide a response structured in the following JSON format, which includes:
- The code block import statements
- The code
- A description explaining the code (documentation)
- The time complexity related to the code, expressed in Big-O notation.

USER PROMPT EXAMPLE: Generate a Python function to add two numbers.
JSON RESPONSE:
```
{
    "documentation": "The function 'add' takes two parameters ('a' and 'b') and returns their sum ('a+b')."
    "imports": "import sys",
    "code": "def add(a, b): return a + b",
    "time_complexity": "O(1)"

}
```

USER PROMPT EXAMPLE: Generate a Python script about binary search.
JSON RESPONSE:
```
{
    "documentation": "The binary search algorithm is an efficient way to find an item from a sorted list. It works by repeatedly dividing the search interval in half. If the value of the search key is less than the middle item, the search continues in the lower half; if it's greater, the search continues in the upper half. This process continues until the value is found or the interval is empty. The binary search function returns the index of the target if found, otherwise -1.",
    "imports": "import sys",
    "code": "def binary_search(arr, target):\n    left, right = 0, len(arr) - 1\n    while left <= right:\n        mid = left + (right - left) // 2\n        if arr[mid] == target:\n            return mid\n        elif arr[mid] < target:\n            left = mid + 1\n        else:\n            right = mid - 1\n    return -1\n"
    "time_complexity": "O(log n)"
}

```

USER PROMPT EXAMPLE: Generate a function to validate a password.
        It checks if password given by the user has a length of at least 8 and
        contains at least one number and one letter.

JSON RESPONSE:
```
{
    "documentation": "The function 'check_password' checks whether the input password has a length of at least 8 characters and contains at least one letter (alphabetic character) and at least one number. It uses regular expressions to ensure that the password contains both alphabetic characters and digits. If the password meets the requirements, the function returns True; otherwise, it returns False.",
    "imports": "import re",
    "code": "def check_password(password):\n    # Check if the length is at least 8 characters\n    if len(password) < 8:\n        return False\n\n    # Check if the password contains at least one letter and one number\n    if not re.search(r'[a-zA-Z]', password):  # Check if there's at least one letter\n        return False\n    if not re.search(r'[0-9]', password):    # Check if there's at least one number\n        return False\n\n    return True\n"
    "time_complexity": "O(n)"
}
```

CODE GENERATION TASK
{user_prompt}

"""

# Prompt input from the user for the coding task

print("User prompt from stdin (insert 0) or user prompt from BigCodeBench (insert 1): ")
user_prompt_mode = int(input())
user_prompt = ""
frame_no = 7
if user_prompt_mode == 0:
    user_prompt = input("Insert user prompt: ")
else:
    user_prompt = instruct_prompt_list[frame_no]

print(f"User prompt: {user_prompt}\n")

problem_definition = role_programmer_prompt.replace("{user_prompt}", user_prompt)

# Instantiate the LLM agent using a specified model type
type_model = 'starcoder2-7b' #'codellama-13b-instruct' #'deepseek-coder-v2-lite-instruct'
agent = get_clone_agent(type_model)

start = time.time() # calcolare il tempo di esecuzione del task
# Get the initial code generation response from the agent
response = get_programmer_first_response(agent, problem_definition)
print("Response\n\n" + response)

# Terminate if the agent produced no response
if "" == response:
    print("End with failure!")
else:
    counts = 0
    final_score = 0
    ai_response = ""
    evaluation = ""

    # Perform evaluation and refinement for a maximum of MAXROUNDS_NO iterations
    for i in range(0, MAX_EVAL_ROUNDS):

        counts = i
        print("Evaluation")

        # Prepare the agent's code response for evaluation
        ai_response = get_formatted_code_solution(response)
        evaluator = get_evaluator(type_model)
        evaluation = eval_code(str(user_prompt), str(ai_response), evaluator)

        print(evaluation)

        # Parse the evaluation to extract individual criteria scores and explanatory feedback
        evaluation_scores = extract_criteria_scores(evaluation)
        evaluation_feedback = extract_explanation(evaluation)
        final_score = calculate_score_code(evaluation_scores)

        print(f"Final code quality score: {final_score:.2f}")

        # If the score is below 85%, instruct the model to refine the code based on feedback
        if final_score < 85 and counts+1 != MAX_EVAL_ROUNDS:
            response = str(
                self_refinement_unique(user_prompt, evaluation_feedback, ai_response)
            )
            print("Response after evaluation" + "\n\n" + response)
        elif final_score > 85 and counts+1 != MAX_EVAL_ROUNDS:
            # Accept the final response if it meets the quality threshold
            print("=================MODEL RESPONSE=================\n" + ai_response)
            if user_prompt_mode == 1:
                print("================CANONICAL SOLUTION================\n" + canonical_solution_list[frame_no])
            break



    # If max iterations are reached and score is still below threshold, accept the latest version
    if counts + 1 == MAX_EVAL_ROUNDS:
        print(f"End with a solution with overall score: {final_score}")
        print(ai_response)

    # === EXECUTION TIME LOGGING ===
    end = time.time()
    elapsed_single = end - start
    print(f"Execution time for LLM: {elapsed_single:.2f}s")

    # === RUNTIME TESTING ===
    print("\n--- Compilation and execution test ---")
    success = save_and_test_code(ai_response)

    if user_prompt_mode == 1:
        # === UNIT TESTING (BIGCODEBENCH) ===
        print("\n--- Run BigCodeBench unit tests ---")

        imports_str = ""
        import ast

        # Convert list of required libraries into import statements
        libs = ast.literal_eval(libs_list[frame_no]) # From string to list
        for value in libs:
            imports_str += "import " + value + "\n"

        test_code = imports_str + test_list[frame_no]

        # Valutazione
        test_results = evaluate_code_with_tests(ai_response, test_code)
        print("All tests passed!" if test_results["passed"] else "Some tests failed.")

    # === STATIC ANALYSIS AND METRICS ===
    cognitive_complexity = get_cognitive_complexity(ai_response)
    time_complexity = extract_time_complexity(response)
    docs = extract_documentation(response)


    # Collect SonarQube metrics (e.g., maintainability, security issues, duplication, etc.)
    metrics_sq_str = ""

    project_key, all_metrics = analyze_code_sonarqube(ai_response)
    metrics_sq_str = ""
    print("#==== SonarQube metrics =====")
    for metric, value in all_metrics.items():
        print(f"{metric}: {value}")
        metrics_sq_str += f"{metric} : {value}\n"


    real_correctness = (100*test_results["tests_passed"]) / test_results["tests_run"]
    print(f"Real correctness: {real_correctness}")

    # === SAVE FINAL OUTPUT AND METRICS TO CSV ===
    if user_prompt_mode == 1:
        save_task_data_to_csv("single-agent_csv_results.csv", frame_no, instruct_prompt_list[frame_no],
                              canonical_solution_list[frame_no], ai_response, docs, cognitive_complexity,
                              time_complexity, evaluation, metrics_sq_str, 1,
                              f"programmer = evaluator = : {type_model}", MAX_EVAL_ROUNDS,
                              elapsed_single, "self-refinement", test_results["tests_passed"], test_results["tests_failed"])
        print("Results saved to single-agent_csv_results.csv")
