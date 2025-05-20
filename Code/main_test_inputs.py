'''Complete Python code'''
from tabulate import tabulate

from Code.metrics import extract_input_values, calulate_time_complexity, get_cognitive_complexity

AGENTS_NO = 2
MAXROUNDS_NO = 5

from LLM_definition import get_clone_agent, get_first_response, get_response, get_discussion_prompt, get_agreement, \
    get_discussion_feedback_prompt, get_first_response_test_inputs, \
    get_discussion_feedback_prompt_test_inputs, get_response_test_inputs
from utility_function import get_formatted_code_solution
from evaluator import eval_code, get_evaluator


def simulate_round(user_prompt, few_shot_prompt, agents, max_rounds):
    # Iniziamo il round
    print(f"User prompt: {user_prompt}\n")

    # Fase 1: Tutti i modelli rispondono al prompt autonomamente

    response = [] #array che contiene le risposte degli agenti
    for i in range(0, AGENTS_NO):
        response.append(get_first_response_test_inputs(agents[i], few_shot_prompt, user_prompt))

    # Print responses
    for i in range(0, AGENTS_NO):
        print(f"Response model {i}: {response[i]}")

    # Fase 2: Dibattito tra i modelli
    round = 1
    while round <= max_rounds:

        # Calcolo metrica di tempo

        time_complexity = []  # keeps time complexity for each response
        import json

        for i in range(0, AGENTS_NO):
            response_json = json.loads(response[i])  # 🔁 parsing della stringa JSON
            input_values = extract_input_values(response_json)
            time_complexity.append(calulate_time_complexity(response_json, input_values))

        for i in range(0, AGENTS_NO):
            print(f"Tempo per risposta {i}: {time_complexity[i]}")

        # Calcolo metrica di leggibilità

        readability_complexity = []  # keeps cognitive metric for each response
        details_readability_complexity = []
        import json

        for i in range(0, AGENTS_NO):
            response_json = json.loads(response[i])  # 🔁 parsing della stringa JSON
            total, details = get_cognitive_complexity(response_json["code"])
            print(tabulate(details, headers=["Complexity", "Node"], tablefmt="fancy_grid"))
            readability_complexity.append(total)
            details_readability_complexity.append(details)

        for i in range(0, AGENTS_NO):
            # Stampa in formato tabellare
            print("\nDettagli della complessità:")
            print(tabulate(details_readability_complexity[i], headers=["Complexity", "Code"], tablefmt="grid"))

        # Costruzione del prompt per la discussione

        debate_prompts = []

        for i in range(0, AGENTS_NO):
            other_responses = [r for j, r in enumerate(response) if j != i]
            other_time_compl = [r for j, r in enumerate(time_complexity) if j != i]
            other_readability_compl = [r for j, r in enumerate(readability_complexity) if j != i]
            debate_prompts.append(
                get_discussion_feedback_prompt_test_inputs(response[i], time_complexity[i], readability_complexity[i], other_responses,
                                            other_readability_compl, other_time_compl))

            # Risposte di entrambi i modelli riguardo ai miglioramenti
        feedback = []

        for i in range(0, AGENTS_NO):
            feedback.append(get_agreement(agents[i], user_prompt, debate_prompts[i]))

        print(f"\nRound {round} - Feedback:")
        # Print feedbacks
        for i in range(0, AGENTS_NO):
            print(f"Feedback model {i}: {feedback[i]}\n")

        # Si verifica se c'è almeno un modello che vuole migliorare la propria risposta
        answers_improvable = []
        for i in range(0, AGENTS_NO):
            if ("yes" in str(feedback[i]).lower() or (
                    "yes" not in str(feedback[i]).lower() and "no" not in str(feedback[i]).lower())):
                answers_improvable.append(i)  # si inseriscono gli indici dei modelli

        # Se non ci sono modelli che vogliono cambiare la risposta allora si è giunti ad un accordo
        if len(answers_improvable) == 0:
            print("Agreement")
            print("\nFinal answer:")
            print(f"{response[0]}\n")
            return response[0]

        # Altrimenti, ogni modello migliora la propria risposta
        for i in answers_improvable:
            other_responses = [r for j, r in enumerate(response) if
                               j != i]  # rimuove dalle risposte quella del modello i
            # ---vedi per eventuale inserimento time complexity e cognitive
            debate_prompts[i] = get_discussion_prompt(response[i], other_responses)
            response[i] = get_response_test_inputs(agents[i], user_prompt, debate_prompts[i])
            print(f"Improved model {i} response: {response[i]}")

        round += 1

        # Se il numero di round è superato, termina senza risposta finale
        if round > max_rounds:
            print(f"\nNot Agreement due to Maximum round ({max_rounds}) achieved.")
            for i in range(0, AGENTS_NO):
                print(f"Answer model {i}: {response[i]}")
            return -1


# MAIN
# Esegui la simulazione con un limite di round
few_shot_prompt = """Provide a response structured in the following JSON format, which includes:
- The code block import statements 
- The code
- A description explaining the code (documentation)
- A list of three example test inputs to test the function with. 
    Each test input should include a list of positional arguments to pass to the function, denoted as 'args'.


EXAMPLE: Generate a Python function to add two numbers.
JSON RESPONSE:
```
{ 
    "documentation": "The function 'add' takes two parameters ('a' and 'b') and returns their sum ('a+b').",
    "imports": "import sys",
    "code": "def add(a, b): return a + b",
    "test_inputs": [
        {
            "args": [3, 5]
        },
        {
            "args": [6, -3]
        },
        {
            "args": [-2, -8]
        }
    ]
}

```

EXAMPLE: Generate a Python script about binary search.
JSON RESPONSE:
```
{
  "documentation": "The binary search algorithm is an efficient way to find an item from a sorted list. It works by repeatedly dividing the search interval in half. If the value of the search key is less than the middle item, the search continues in the lower half; if it's greater, the search continues in the upper half. This process continues until the value is found or the interval is empty. The binary search function returns the index of the target if found, otherwise -1.",
  "imports": "import sys",
  "code": "def binary_search(arr, target):\n    left, right = 0, len(arr) - 1\n    while left <= right:\n        mid = left + (right - left) // 2\n        if arr[mid] == target:\n            return mid\n        elif arr[mid] < target:\n            left = mid + 1\n        else:\n            right = mid - 1\n    return -1\n\n# Example usage\narr = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]\ntarget = 7\nresult = binary_search(arr, target)\nif result != -1:\n    print(f'Element found at index {result}')\nelse:\n    print('Element not found')",
  "test_inputs": [
    {
        "args": [[1, 3, 5, 7, 9], 5]
    },
    {
        "args": [[1, 3, 5, 7, 9], 9]
    },
    {
        "args": [[1, 3, 5, 7, 9], 2]
    }
  ]
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
    "code": "def check_password(password):\n    if len(password) < 8:\n        return False\n    if not re.search(r'[a-zA-Z]', password):\n        return False\n    if not re.search(r'[0-9]', password):\n        return False\n    return True\n\n# Example usage\npassword = input('Enter your password: ')\n\nif check_password(password):\n    print('The password is valid.')\nelse:\n    print('The password is not valid. It must have at least 8 characters, and contain at least one letter and one number.')",
    "test_inputs": [
        {
            "args": ["password123"]
        },
        {
            "args": ["short"]
        },
        {
            "args": ["noDigits"]
        }
    ]
}

```

"""
user_prompt = input()
# Initialize agents
typeModel = 'codellama-7b-instruct'
agents = []

for i in range(0, AGENTS_NO):
    agents.append(get_clone_agent(typeModel))

# Round
debate_response = str(simulate_round(user_prompt, few_shot_prompt, agents, max_rounds=MAXROUNDS_NO))
if("-1" in debate_response):
    print("End debate with failure!")
else:
    print("Evaluation")
    # Evaluation
    ai_response = get_formatted_code_solution({debate_response})
    evaluator = get_evaluator(typeModel)
    eval_code(str(user_prompt), str(ai_response), evaluator)
