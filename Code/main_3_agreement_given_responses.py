'''MAIN'''
import sys

# Import core modules used for debate simulation, agent creation, and code evaluation

from Debate_strategies import simulate_round, AGENTS_NO, MAXROUNDS_NO, simulate_round_k_solutions, \
    simulate_complete_round, after_evaluation_debate
from LLM_definition import getCloneAgent, get_response_to_evaluate
from evaluator import eval_code, get_evaluator, extract_criteria_scores, calculate_score_code, extract_explanation

# Few-shot prompt to guide the LLM agents on how to structure their responses in JSON format
# It includes multiple examples of correct outputs for different types of coding tasks

import lmstudio as lms
SERVER_API_HOST = "localhost:2345"

# This must be the *first* convenience API interaction (otherwise the SDK
# implicitly creates a client that accesses the default server API host)
lms.configure_default_client(SERVER_API_HOST)

# Note: the dedicated configuration API was added in lmstudio-python 1.3.0
# For compatibility with earlier SDK versions, it is still possible to use
# lms.get_default_client(SERVER_API_HOST) to configure the default client

few_shot_prompt = """Provide a response structured in the following JSON format, which includes:
- The code block import statements 
- The code
- A description explaining the code (documentation)
- The time complexity related to the code, expressed in Big-O notation.

EXAMPLE: Generate a Python function to add two numbers.
JSON RESPONSE:
```
{ 
    "documentation": "The function 'add' takes two parameters ('a' and 'b') and returns their sum ('a+b')." 
    "imports": "import sys",
    "code": "def add(a, b): return a + b",
    "time_complexity": "O(1)"

}
```

EXAMPLE: Generate a Python script about binary search.
JSON RESPONSE:
```
{
    "documentation": "The binary search algorithm is an efficient way to find an item from a sorted list. It works by repeatedly dividing the search interval in half. If the value of the search key is less than the middle item, the search continues in the lower half; if it's greater, the search continues in the upper half. This process continues until the value is found or the interval is empty. The binary search function returns the index of the target if found, otherwise -1.",
    "imports": "import sys",
    "code": "def binary_search(arr, target):\n    left, right = 0, len(arr) - 1\n    while left <= right:\n        mid = left + (right - left) // 2\n        if arr[mid] == target:\n            return mid\n        elif arr[mid] < target:\n            left = mid + 1\n        else:\n            right = mid - 1\n    return -1\n\n# Example usage\narr = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]\ntarget = 7\nresult = binary_search(arr, target)\nif result != -1:\n    print(f'Element found at index {result}')\nelse:\n    print('Element not found')"
    "time_complexity": "O(log n)"
}

```

EXAMPLE: Generate a function to validate a password. 
        It checks if password given by the user has a length of at least 8 and 
        contains at least one number and one letter.

JSON RESPONSE:
```
{
    "documentation": "The function 'check_password' checks whether the input password has a length of at least 8 characters and contains at least one letter (alphabetic character) and at least one number. It uses regular expressions to ensure that the password contains both alphabetic characters and digits. If the password meets the requirements, the function returns True; otherwise, it returns False.",
    "imports": "import re",
    "code": "def check_password(password):\n    # Check if the length is at least 8 characters\n    if len(password) < 8:\n        return False\n\n    # Check if the password contains at least one letter and one number\n    if not re.search(r'[a-zA-Z]', password):  # Check if there's at least one letter\n        return False\n    if not re.search(r'[0-9]', password):    # Check if there's at least one number\n        return False\n\n    return True\n\n# Example usage\npassword = input('Enter your password: ')\n\nif check_password(password):\n    print('The password is valid.')\nelse:\n    print('The password is not valid. It must have at least 8 characters, and contain at least one letter and one number.')"
    "time_complexity": "O(n)"
}
```

"""
strategy_debate = input()
sys.stdin.buffer.flush() # flush buffer stdin
user_prompt = input()
print(f"User prompt: {user_prompt}\n")

# Initialize the list of agents using the selected model
typeModel = 'codellama-7b-instruct' #'llama-3.2-3b-instruct' # You can switch to a different model, e.g., 'codellama-7b-instruct', 'qwen2.5-coder-3b-instruct'
typeEvalModel = 'codellama-7b-instruct'
agents = []

# Clone agents based on the configured number of agents (AGENTS_NO)

for i in range(0, AGENTS_NO):
    agents.append(getCloneAgent(typeModel))

debate_response = ""

# Simulate a multi-agent debate round with the user prompt and the few-shot examples
if strategy_debate == "0":
    debate_response = str(simulate_round(user_prompt, few_shot_prompt, agents, max_rounds=MAXROUNDS_NO))
elif strategy_debate == '1':
    debate_response = str(simulate_round_k_solutions(user_prompt, few_shot_prompt, agents, max_rounds=MAXROUNDS_NO))
elif strategy_debate == '2':
    debate_response = str(simulate_complete_round(user_prompt, few_shot_prompt, agents, max_rounds=MAXROUNDS_NO))
else:
    print("ERRORE INPUT: 0, 1, 2 AMMESSI")
    exit(-1)  # input error
# If no consensus is reached during the debate, end the process with a failure message
if "-1" == debate_response:
    print("End debate with failure!")
else:
    i = 1
    final_score = 0
    ai_response = ""
    # Evaluate the final proposed solution from the agents
    for i in range(1, MAXROUNDS_NO):
        print("Evaluation")

        # Extract the candidate response (code+imports) to evaluate
        ai_response = get_response_to_evaluate(debate_response)
        evaluator = get_evaluator(typeEvalModel)
        evaluation = eval_code(str(user_prompt), str(ai_response), evaluator)

        print(evaluation)

        # Extract individual evaluation scores from the evaluation output and
        # calculate the final aggregate score for the generated code
        evaluation_scores = extract_criteria_scores(evaluation)
        evaluation_feedback = extract_explanation(evaluation)
        final_score = calculate_score_code(evaluation_scores)

        print(f"Final code quality score: {final_score:.2f}")

        # If the score is below the acceptable threshold (e.g., 90), trigger another debate round
        if final_score < 90:
            debate_response = str(after_evaluation_debate(user_prompt, few_shot_prompt, evaluation_feedback, ai_response, agents, strategy_debate, max_rounds=MAXROUNDS_NO)) #vedi s emettere few_shot_prompt per il formato
        else:
            print(ai_response)  # print the accepted final response
            break

    if i == MAXROUNDS_NO:   # solution provided has a score lower than 90
        print(f"End debate with a solution with overall score: {final_score}")
        print(ai_response)
