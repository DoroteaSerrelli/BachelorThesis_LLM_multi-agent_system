"""MAIN"""

import sys

from Code.utility_function import analyze_code_sonarqube, get_all_sonar_metrics
from evaluation_bigcodebench import instruct_prompt_list, canonical_solution_list, test_list

from metrics import extract_time_complexity, get_cognitive_complexity

# Import core modules used for debate simulation, agent creation, and code evaluation

from Debate_strategies import AGENTS_NO, after_evaluation_debate, developers_debate, developers_debate_mixed_strategy
from LLM_definition import get_clone_agent
from utility_function import get_formatted_code_solution, save_and_test_code, evaluate_code_with_tests, \
    save_task_data_to_csv, extract_documentation
from evaluator import eval_code, get_evaluator, extract_criteria_scores, calculate_score_code, extract_explanation

# Few-shot prompt to guide the LLM agents on how to structure their responses in JSON format
# It includes multiple examples of correct outputs for different types of coding tasks

import lmstudio as lms
SERVER_API_HOST = "localhost:1234"  #server lmstudio port <--- 2345

# This must be the *first* convenience API interaction (otherwise the SDK
# implicitly creates a client that accesses the default server API host)
lms.configure_default_client(SERVER_API_HOST)

# Note: the dedicated configuration API was added in lmstudio-python 1.3.0
# For compatibility with earlier SDK versions, it is still possible to use
# lms.get_default_client(SERVER_API_HOST) to configure the default client

# Maximum number of refinement response rounds allowed based on evaluator feedback, before ending the debate
# with a partial solution.
MAX_EVAL_ROUNDS = 3

role_programmer_prompt = """You are an AI expert programmer that writes code or helps to review code for bugs,
based on the user request. Given a code generation task, inserted in **CODE GENERATION TASK** section, provide a response structured in the following JSON schema:

schema_complexity = {
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

CODE GENERATION TASK EXAMPLE: Generate a Python function to add two numbers.
JSON RESPONSE:
```
{
    "documentation": "The function 'add' takes two parameters ('a' and 'b') and returns their sum ('a+b')."
    "imports": "import sys",
    "code": "def add(a, b): return a + b",
    "time_complexity": "O(1)"

}
```

CODE GENERATION TASK EXAMPLE: Generate a Python script about binary search.
JSON RESPONSE:
```
{
    "documentation": "The binary search algorithm is an efficient way to find an item from a sorted list. It works by repeatedly dividing the search interval in half. If the value of the search key is less than the middle item, the search continues in the lower half; if it's greater, the search continues in the upper half. This process continues until the value is found or the interval is empty. The binary search function returns the index of the target if found, otherwise -1.",
    "imports": "import sys",
    "code": "def binary_search(arr, target):\n    left, right = 0, len(arr) - 1\n    while left <= right:\n        mid = left + (right - left) // 2\n        if arr[mid] == target:\n            return mid\n        elif arr[mid] < target:\n            left = mid + 1\n        else:\n            right = mid - 1\n    return -1\n"
    "time_complexity": "O(log n)"
}

```

CODE GENERATION TASK EXAMPLE: Generate a function to validate a password.
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

print("Choose strategy debate (0, 1, 2): ")
strategy_debate = input()
sys.stdin.buffer.flush() # flush buffer stdin
print("User prompt from stdin (insert 0) or user prompt from BigCodeBench (insert 1): ")
user_prompt_mode = int(input())
user_prompt = ""
frame_no = 7
if user_prompt_mode == 0:
    sys.stdin.buffer.flush() # flush buffer stdin
    user_prompt = input("Insert user prompt: ")
else:
    user_prompt = instruct_prompt_list[frame_no]

print(f"User prompt: {user_prompt}\n")

# Initialize the list of agents using the selected model
types_model = ['codellama-7b-instruct'] * AGENTS_NO # You can switch to a different model, e.g., 'qwen2.5-coder-3b-instruct', 'deepseek-coder-v2-lite-instruct'

type_evaluator_model = 'codellama-7b-instruct' #'deepseek-coder-v2-lite-instruct'
agents = []

# Clone agents based on the configured number of agents (AGENTS_NO)

for i in range(0, AGENTS_NO):
    agents.append(get_clone_agent(types_model[i]))

debate_response = ""

# Simulate a multi-agent debate round with the user prompt and the few-shot examples
if strategy_debate == "0":
    debate_response = str(developers_debate(agents, user_prompt, role_programmer_prompt, strategy_debate))
elif strategy_debate == '1':
    debate_response = str(developers_debate(agents, user_prompt, role_programmer_prompt, strategy_debate))
elif strategy_debate == '2':
    debate_response = str(developers_debate_mixed_strategy(agents, user_prompt, role_programmer_prompt))
else:
    # input error
    print("INPUT ERROR: INSERT ONLY 0, 1, 2")
    exit(-1)

# If no consensus is reached during the debate, end the process with a failure message
if debate_response == "-1":
    print("End debate with failure!")
else:
    i = 0
    final_score = 0
    ai_response = ""
    evaluation = ""
    # Evaluate the final proposed solution from the agents
    for i in range(0, MAX_EVAL_ROUNDS):
        print("Evaluation")

        # Extract the candidate response (code+imports) to evaluate
        ai_response = get_formatted_code_solution(debate_response)
        evaluator = get_evaluator(type_evaluator_model)
        evaluation = eval_code(str(user_prompt), str(ai_response), evaluator)

        print(evaluation)

        # Extract individual evaluation scores from the evaluation output and
        # calculate the final aggregate score for the generated code
        evaluation_scores = extract_criteria_scores(evaluation)
        evaluation_feedback = extract_explanation(evaluation)
        final_score = calculate_score_code(evaluation_scores)

        print(f"Final code quality score: {final_score:.2f}")

        # If the score is below the acceptable threshold (e.g., 85), trigger another debate round
        if final_score < 85:
            debate_response = str(after_evaluation_debate(user_prompt, role_programmer_prompt, evaluation_feedback, ai_response, agents, strategy_debate))
        else:
            print("================OUTPUT LLM MULTI-AGENT SYSTEM================\n" + ai_response)  # print the accepted final response
            print("================CANONICAL SOLUTION================\n" + canonical_solution_list[frame_no])
            break

    if i == MAX_EVAL_ROUNDS:   # solution provided has a score lower than 90
        print(f"End debate with a partial solution with overall score: {final_score}")
        print(ai_response)

    # Esecuzione code snippet

    print("\n--- Test di compilazione ed esecuzione del codice generato ---")
    success = save_and_test_code(ai_response)

    if user_prompt_mode == 1:

        print("\n--- Esecuzione test codice output del sistema con i test unitari di BigCodeBenchmark --- ")

        test_code = test_list[frame_no]

        # Valutazione
        test_results = evaluate_code_with_tests(ai_response, test_code)
        print("Il codice generato dal sistema LLM multi-agente ha passato tutti i test!" if test_results["passed"] else "Il codice generato dal sistema LLM multi-agente non ha passato tutti i test")

    # Salvare i risultati in un file csv
    cognitive_complexity = get_cognitive_complexity(debate_response)
    time_complexity = extract_time_complexity(debate_response)
    docs = extract_documentation(debate_response)
    if user_prompt_mode == 1:
        save_task_data_to_csv("csv_results.csv", frame_no, instruct_prompt_list[frame_no], canonical_solution_list[frame_no], ai_response, docs, cognitive_complexity, time_complexity, evaluation, test_results["tests_passed"], test_results["tests_failed"])
        print("I dati sono stati salvati nel file csv_results.csv")

    project_key, complexity, all_metrics = analyze_code_sonarqube(ai_response)

    print("Cognitive_complexity SONARQUBE: " + str(complexity))

    print("Altre metriche SonarQube:")
    for metric, value in all_metrics.items():
        print(f"{metric}: {value}")
