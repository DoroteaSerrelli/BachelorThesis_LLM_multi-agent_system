'''Python code to simulate agent debate'''

from LLM_definition import getCloneAgent, get_first_response, get_response, getDiscussionPrompt, get_agreement, \
    getDiscussionFeedbackPrompt


def simulate_round(user_prompt, few_shot_prompt, model_1, model_2, max_rounds):

    # Iniziamo il round
    print(f"User prompt: {user_prompt}\n")

    # Fase 1: Entrambi i modelli rispondono al prompt autonomamente

    response_1 = get_first_response(model1, few_shot_prompt, user_prompt)
    response_2 = get_first_response(model2, few_shot_prompt, user_prompt)

    print(f"Response first model: {response_1}")
    print(f"Response second model: {response_2}\n")

    # Fase 2: Dibattito tra i due modelli
    round = 1
    while round <= max_rounds:
        # Costruzione del prompt per la discussione

        deb_prompt_1 = getDiscussionFeedbackPrompt(response_1, [response_2])
        deb_prompt_2 = getDiscussionFeedbackPrompt(response_2, [response_1])

        # Risposte di entrambi i modelli riguardo ai miglioramenti
        feedback_1 = get_agreement(model_1, user_prompt, deb_prompt_1)
        feedback_2 = get_agreement(model_2, user_prompt, deb_prompt_2)

        print(f"\nRound {round} - Feedback:")
        print(f"Feedback first model: {feedback_1}")
        print(f"Feedback second model: {feedback_2}\n")

        # Se entrambi i modelli sono d'accordo che non ci sono miglioramenti, termina
        if "no" in str(feedback_1).lower() and "no" in str(feedback_2).lower():
            print("Agreement between each model.")
            print("\nFinal answer:")
            print(f"{response_1}\n")
            break

        # Altrimenti, ogni modello migliora la propria risposta
        if "yes" in str(feedback_1).lower():
            deb_prompt_1 = getDiscussionPrompt(response_1, [response_2])
            response_1 = get_response(model_1, user_prompt, deb_prompt_1)
            print("Improved agent 1 response: " + response_1)
        if "yes" in str(feedback_2).lower():
            deb_prompt_2 = getDiscussionPrompt(response_2, [response_1])
            response_2 = get_response(model_2, user_prompt, deb_prompt_2)
            print("Improved agent 2 response: " + response_2)
        round += 1

    # Se il numero di round è superato, termina senza risposta finale
    if round > max_rounds:
        print(f"\nMaximum round ({max_rounds}) achieved. Final (partial) answer:")
        print(f"Answer first model: {response_1}")
        print(f"Answer second model: {response_2}")


# MAIN
# Esegui la simulazione con un limite di round
few_shot_prompt = """Provide a response structured in the following JSON format, which includes:
- The code block import statements 
- The code
- A description explaining the code

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
    "documentation": "The function 'verifica_password' checks whether the input password has a length of at least 8 characters and contains at least one letter (alphabetic character) and at least one number. It uses regular expressions to ensure that the password contains both alphabetic characters and digits. If the password meets the requirements, the function returns True; otherwise, it returns False.",
    "imports": "import re",
    "code": "def verifica_password(password):\n    # Check if the length is at least 8 characters\n    if len(password) < 8:\n        return False\n\n    # Check if the password contains at least one letter and one number\n    if not re.search(r'[a-zA-Z]', password):  # Check if there's at least one letter\n        return False\n    if not re.search(r'[0-9]', password):    # Check if there's at least one number\n        return False\n\n    return True\n\n# Example usage\npassword = input('Enter your password: ')\n\nif verifica_password(password):\n    print('The password is valid.')\nelse:\n    print('The password is not valid. It must have at least 8 characters, and contain at least one letter and one number.')"
}
```

QUESTION: 
"""
user_prompt = "Generate a Java function to calculate the current date."
# Inizializza i due modelli LLaMA
typeModel = 'codellama-7b-instruct'
model1 = getCloneAgent(typeModel)
model2 = getCloneAgent(typeModel)

simulate_round(user_prompt, few_shot_prompt, model1, model2, max_rounds=3)
