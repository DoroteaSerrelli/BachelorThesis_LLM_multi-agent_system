'''Complete Python code'''

AGENTS_NO = 2
MAXROUNDS_NO = 5

from LLM_definition import getCloneAgent, get_first_response, get_response, getDiscussionPrompt, get_agreement, \
    getDiscussionFeedbackPrompt, get_response_to_evaluate
from Sperimentazione.Sperimentazione_ChatGPT.evaluator import eval_code, get_evaluator


def simulate_round(user_prompt, few_shot_prompt, agents, max_rounds):
    # Iniziamo il round
    print(f"User prompt: {user_prompt}\n")

    # Fase 1: Tutti i modelli rispondono al prompt autonomamente

    response = [] #array che contiene le risposte degli agenti
    for i in range(0, AGENTS_NO):
        response.append(get_first_response(agents[i], few_shot_prompt, user_prompt))

    # Print responses
    for i in range(0, AGENTS_NO):
        print(f"Response model {i}: {response[i]}")

    # Fase 2: Dibattito tra i modelli
    round = 1
    while round <= max_rounds:
        # Costruzione del prompt per la discussione

        debate_prompts = []

        for i in range(0, AGENTS_NO):
            other_responses = [r for j, r in enumerate(response) if j != i]
            debate_prompts.append(getDiscussionFeedbackPrompt(response[i], other_responses))



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
            if ("yes" in str(feedback[i]).lower() or ("yes" not in str(feedback[i]).lower() and "no" not in str(feedback[i]).lower())):
                answers_improvable.append(i) #si inseriscono gli indici dei modelli

        # Se non ci sono modelli che vogliono cambiare la risposta allora si è giunti ad un accordo
        if(len(answers_improvable) == 0):
            print("Agreement")
            print("\nFinal answer:")
            print(f"{response[0]}\n")
            return response[0]

        # Altrimenti, ogni modello migliora la propria risposta
        for i in answers_improvable:
            other_responses = [r for j, r in enumerate(response) if j != i] # rimuove dalle risposte quella del modello i
            debate_prompts[i] = getDiscussionPrompt(response[i], other_responses)
            response[i] = get_response(agents[i], user_prompt, debate_prompts[i])
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

EXAMPLE: Generate a Python function to add two numbers.
JSON RESPONSE:
```
{ 
    "documentation": "The function 'add' takes two parameters ('a' and 'b') and returns their sum ('a+b')." 
    "imports": "import sys",
    "code": "def add(a, b): return a + b",

}
```

EXAMPLE: Generate a Python script about binary search.
JSON RESPONSE:
```
{
  "documentation": "The binary search algorithm is an efficient way to find an item from a sorted list. It works by repeatedly dividing the search interval in half. If the value of the search key is less than the middle item, the search continues in the lower half; if it's greater, the search continues in the upper half. This process continues until the value is found or the interval is empty. The binary search function returns the index of the target if found, otherwise -1.",
  "imports": "import sys",
  "code": "def binary_search(arr, target):\n    left, right = 0, len(arr) - 1\n    while left <= right:\n        mid = left + (right - left) // 2\n        if arr[mid] == target:\n            return mid\n        elif arr[mid] < target:\n            left = mid + 1\n        else:\n            right = mid - 1\n    return -1\n\n# Example usage\narr = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]\ntarget = 7\nresult = binary_search(arr, target)\nif result != -1:\n    print(f'Element found at index {result}')\nelse:\n    print('Element not found')"
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
}
```

"""
user_prompt = input()
# Initialize agents
typeModel = 'codellama-7b-instruct'
agents = []

for i in range(0, AGENTS_NO):
    agents.append(getCloneAgent(typeModel))

# Round
debate_response = str(simulate_round(user_prompt, few_shot_prompt, agents, max_rounds=MAXROUNDS_NO))
if("-1" in debate_response):
    print("End debate with failure!")
else:
    print("Evaluation")
    # Evaluation
    ai_response = get_response_to_evaluate({debate_response})
    evaluator = get_evaluator(typeModel)
    eval_code(str(user_prompt), str(ai_response), evaluator)
