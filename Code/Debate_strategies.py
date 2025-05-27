"""
    Helper functions to manage the debate between multiple LLM agents
    collaborating on a source code generation task.
    The debate process aims to iteratively refine and evaluate candidate solutions,
    based on cognitive (readability) and time complexity, until a consensus is reached.
"""
import json

from tabulate import tabulate

from Code.response_JSON_schema import schema_feedback
# Imports
from LLM_definition import (
    get_programmer_first_response,
    get_response,
    get_self_refinement_prompt
)

from metrics import get_cognitive_complexity, extract_time_complexity
from utility_function import equals_cognitive_complexity, equals_time_complexity, \
    get_random_element, get_k_responses, get_feedback_value, get_formatted_code_solution

# Number of LLM agents participating in the debate
AGENTS_NO = 2

# Maximum number of allowed debate rounds before falling back to majority voting
MAXROUNDS_NO = 3


def developers_debate(programmers, user_prompt, programmer_prompt, strategy_choosen, max_rounds=MAXROUNDS_NO):
    # programmers = lista di agenti programmatori, programmer_prompt = il prompt del programmatore
    # max_rounds = massimo numero di round di dibattito

    problem_definition = programmer_prompt.replace("{user_prompt}", user_prompt)
    responses = []

    for programmer in programmers:
        responses.append(get_programmer_first_response(programmer, problem_definition))

    # Display all initial responses
    i = 0
    for response in responses:
        print(f"Response developer {i}: {response}")
        i += 1

    current_round = 0
    while current_round <= max_rounds:
        # === Measure readability (cognitive complexity) of each response ===
        readability_complexity = []  # Stores total cognitive complexity for each response
        details_readability_complexity = []  # Stores node-level breakdown of complexity

        for i in range(AGENTS_NO):
            response_json = json.loads(responses[i])  # Parse JSON response
            total, details = get_cognitive_complexity(response_json["code"])
            print(tabulate(details, headers=["Complexity", "Node"], tablefmt="fancy_grid"))
            readability_complexity.append(total)
            details_readability_complexity.append(details)

        # I programmatori non possono ignorare la sintassi. Rimuovere le risposte con cognitive complexity pari a -1: errori sintattici

        counter = 0

        responses_allowed = {}  # le risposte che hanno cognitive complexity != -1
        readability_complexity_allowed = {}  # i valori di cognitive complexity delle risposte che hanno cognitive complexity != -1

        for i in range(0, AGENTS_NO):
            if readability_complexity[i] != -1:
                counter += 1
                responses_allowed[i] = responses[i]
                readability_complexity_allowed[i] = readability_complexity[i]

        # ====== Costruzione prompt dibattito ========

        # Formattazione per prompt di dibattito
        formatted_responses = get_formatted_responses(responses_allowed, readability_complexity_allowed, counter)
        debate_prompt = get_refined_debate_prompt(counter, user_prompt, formatted_responses)

        print("DEBATE_PROMPT OTTENUTO: " + debate_prompt)

        # Ottengo le soluzioni votate
        # === Collect feedback from each agent (which solution they prefer) ===
        debate_response = []
        for i in range(AGENTS_NO):
            debate_response.append(get_feedback_value(get_refined_agreement(programmers[i], debate_prompt)))

        # Stampa risposte
        print(f"\nRound {current_round} - Voting")
        for i in range(0, AGENTS_NO):
            print(f"Feedback model {i}: {debate_response[i]}\n")

        # Si verifica se c'è convergenza
        possible_solutions = set(debate_response)  # Unique solutions selected by the agents

        if len(possible_solutions) == 0:  # Tutte le risposte generate dai modelli sono sintatticamente errate
            return "-1"  # Dibattito fallito

        if len(possible_solutions) == 1:
            for var in possible_solutions:
                if 0 <= var < AGENTS_NO:
                    print("Agreement")
                    print("\nFinal answer:")

                    solution = responses[int(var)]
                    print(solution)
                    return solution  # Return the agreed-upon solution
                print("VOTING ERROR FOR SOLUTION NUMBER " + str(var))

        if strategy_choosen == 0:
            # SI PASSA AL SELF-REFINEMENT

            responses = do_self_refinement(programmers, responses, readability_complexity, user_prompt)
            debate_response.clear()
            readability_complexity.clear()
            details_readability_complexity.clear()

            i = 0
            for response in responses:
                print(f"Response self-refined developer {i}: {response}")
                i += 1

        if strategy_choosen == 1:
            # SI PASSA ALL'INSTANT RUNOFF VOTING
            responses = do_instant_runoff_voting(programmers, debate_response, responses_allowed, readability_complexity, user_prompt)

            if len(responses) == 1:
                for var in responses:

                    print("Agreement")
                    print("\nFinal answer:")

                    solution = responses[int(var)]
                    print(solution)
                    return solution  # Return the agreed-upon solution


            debate_response.clear()
            readability_complexity.clear()
            details_readability_complexity.clear()

            i = 0
            for response in responses:
                print(f"Response instant_runoff_voting developer {i}: {response}")
                i += 1

        current_round += 1

    # === If max rounds exceeded, apply majority voting to resolve ===
    vote_index = majority_voting(responses_allowed)
    return responses[int(vote_index)]


def developers_debate_mixed_strategy(programmers, user_prompt, programmer_prompt, max_rounds=MAXROUNDS_NO):
    # programmers = lista di agenti programmatori, programmer_prompt = il prompt del programmatore
    # max_rounds = massimo numero di round di dibattito

    problem_definition = programmer_prompt.replace("{user_prompt}", user_prompt)
    responses = []

    for programmer in programmers:
        responses.append(get_programmer_first_response(programmer, problem_definition))

    # Display all initial responses
    i = 0
    for response in responses:
        print(f"Response developer {i}: {response}")
        i += 1

    current_round = 0
    divergence_round = 0
    while current_round <= max_rounds:
        # === Measure readability (cognitive complexity) of each response ===
        readability_complexity = []  # Stores total cognitive complexity for each response
        details_readability_complexity = []  # Stores node-level breakdown of complexity

        for i in range(AGENTS_NO):
            response_json = json.loads(responses[i])  # Parse JSON response
            total, details = get_cognitive_complexity(response_json["code"])
            print(tabulate(details, headers=["Complexity", "Node"], tablefmt="fancy_grid"))
            readability_complexity.append(total)
            details_readability_complexity.append(details)

        # I programmatori non possono ignorare la sintassi. Rimuovere le risposte con cognitive complexity pari a -1: errori sintattici

        counter = 0

        responses_allowed = {}  # le risposte che hanno cognitive complexity != -1
        readability_complexity_allowed = {}  # i valori di cognitive complexity delle risposte che hanno cognitive complexity != -1

        for i in range(0, AGENTS_NO):
            if readability_complexity[i] != -1:
                counter += 1
                responses_allowed[i] = responses[i]
                readability_complexity_allowed[i] = readability_complexity[i]

        # ====== Costruzione prompt dibattito ========

        # Formattazione per prompt di dibattito
        formatted_responses = get_formatted_responses(responses_allowed, readability_complexity_allowed, counter)
        debate_prompt = get_refined_debate_prompt(counter, user_prompt, formatted_responses)

        print("DEBATE_PROMPT OTTENUTO: " + debate_prompt)

        # Ottengo le soluzioni votate
        # === Collect feedback from each agent (which solution they prefer) ===
        debate_response = []
        for i in range(AGENTS_NO):
            debate_response.append(get_feedback_value(get_refined_agreement(programmers[i], debate_prompt)))

        # Stampa risposte
        print(f"\nRound {current_round} - Voting")
        for i in range(0, AGENTS_NO):
            print(f"Feedback model {i}: {debate_response[i]}\n")

        # Si verifica se c'è convergenza
        possible_solutions = set(debate_response)  # Unique solutions selected by the agents

        if len(possible_solutions) == 0:  # Tutte le risposte generate dai modelli sono sintatticamente errate
            return "-1"  # Dibattito fallito

        if len(possible_solutions) == 1:
            for var in possible_solutions:
                if 0 <= var < AGENTS_NO:
                    print("Agreement")
                    print("\nFinal answer:")

                    solution = responses[int(var)]
                    print(solution)
                    return solution  # Return the agreed-upon solution
                print("VOTING ERROR FOR SOLUTION NUMBER " + str(var))

        divergence_round += 1

        if divergence_round >= 2:
            k_responses = []
            # Verifico se tutte le soluzioni hanno uguale complessità di tempo e uguale complessità di leggibilità
            k_responses = get_k_responses(responses, debate_response)
            k_readability_complexity = {}

            #Inserisco le chiavi

            for var in k_responses:
                if var not in k_readability_complexity:
                    k_readability_complexity[int(var)] = 0

            # Inserisco i valori di cognitive complexity

            keys = k_readability_complexity.keys()
            for i in keys:
                k_readability_complexity[i] = readability_complexity[int(i)]

            if equals_time_complexity(k_responses) and equals_cognitive_complexity(k_readability_complexity):
                solution = str(get_random_element(k_responses))
                print("Agreement between equivalent solution")
                print("\nFinal answer:")

                print(solution)
                return solution  # Return the agreed-upon solution
            else:
                # SI PASSA AL SELF-REFINEMENT
                responses = do_self_refinement(programmers, responses, readability_complexity, user_prompt)
                debate_response.clear()
                readability_complexity.clear()
                details_readability_complexity.clear()

                i = 0
                for response in responses:
                    print(f"Response self-refined developer {i}: {response}")
                    i += 1
                divergence_round = 0

        else:
            # SI PASSA ALL'INSTANT RUNOFF VOTING

            responses = do_instant_runoff_voting(programmers, debate_response, responses_allowed, readability_complexity, user_prompt)

            if len(responses) == 1:
                for var in responses:

                    print("Agreement")
                    print("\nFinal answer:")

                    solution = responses[int(var)]
                    print(solution)
                    return solution  # Return the agreed-upon solution


            debate_response.clear()
            readability_complexity.clear()
            details_readability_complexity.clear()

            i = 0
            for response in responses:
                print(f"Response instant_runoff_voting developer {i}: {response}")
                i += 1

        current_round += 1

        # === If max rounds exceeded, apply majority voting to resolve ===
    vote_index = majority_voting(responses_allowed)
    return responses[int(vote_index)]



# === Self-refinement ===

def do_self_refinement(agents, responses, readability_complexity, user_prompt):
    """
        Allows each agent to refine its own response based on the others' answers.

        This is used when agents disagree, encouraging evolution of solutions toward consensus.
    """

    debate_prompts = [None] * AGENTS_NO

    for i in range(AGENTS_NO):
        # Provide each agent with all other responses except its own
        other_responses = [r for j, r in enumerate(responses) if j != i]

        # Rimuovere le risposte con cognitive complexity pari a -1: errori sintattici

        counter = 0

        other_responses_allowed = {}  # le risposte che hanno cognitive complexity != -1

        for i in range(0, AGENTS_NO):
            if readability_complexity[i] != -1:
                counter += 1
                other_responses_allowed[i] = other_responses[i]


        # Construct the prompt to trigger self-refinement

        if readability_complexity[i] != -1:
            debate_prompts[i] = get_self_refinement_prompt(responses[i], user_prompt, other_responses_allowed)
            print(f"SELF_REFINEMENT DEBATE PER AGENTE {i}: {debate_prompts[i]}")
            responses[i] = get_response(agents[i], debate_prompts[i])
        else:# se ha dato nessuna risposta
            debate_prompts[i] = get_self_refinement_prompt("", user_prompt, other_responses_allowed)
            print(f"SELF_REFINEMENT DEBATE PER AGENTE {i}: {debate_prompts[i]}")
            responses[i] = get_response(agents[i], debate_prompts[i])

        # Generate improved response
        print(f"Improved model {i} response: {responses[i]}")

    return responses





# === Fallback: Majority Voting ===
def majority_voting(feedback):
    """
        Fallback strategy that selects the most popular response when no agreement is reached.

        - Tallies votes for each solution.
        - In case of a tie or invalid votes, returns failure indicator (-1).
    """

    votes = {}
    for agent_feedback in feedback:
        try:
            agent_index = int(agent_feedback)
            votes[agent_index] = votes.get(agent_index, 0) + 1
        except ValueError:
            # Handle the case where an element in feedback is not a valid integer
            return str(-1)

    if not votes:
        return str(-1)  # No valid votes cast

    max_votes = 0
    winner = -1
    winner_count = 0

    for agent, vote_count in votes.items():
        if vote_count > max_votes:
            max_votes = vote_count
            winner = agent
            winner_count = 1
        elif vote_count == max_votes:
            winner_count += 1

    if winner_count == 1:
        return winner
    else:
        return str(-1)  # Tie




'''
    Initiates a post-evaluation debate phase based on prior feedback.
    
    - Takes original user prompt, previous code, and evaluator feedback.
    - Reformulates a refinement prompt for agents.
    - Selects a debate strategy (normal, k-solution, or extended).
    - Produces a revised solution incorporating evaluator insights.
    
    Useful in evaluation pipelines where external agents (e.g., evaluators) 
    identify problems to fix collaboratively.
'''

def after_evaluation_debate(user_prompt, few_shot_prompt, feedback_evaluator, previous_code, programmers, strategy_debate, max_rounds=MAXROUNDS_NO):
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
            -   *Cognitive Complexity*: The cognitive complexity of the refined code must be between 0 and 10 (inclusive). Simplify the logic and structure of the code to enhance its readability and maintainability, without compromising correctness or time complexity.

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
            
            Output ONLY the JSON object. Do not include any extra text outside the JSON block.
            
            EXAMPLE: Generate a Python script about binary search.
            JSON RESPONSE:
            ```
            {
                "documentation": "The binary search algorithm is an efficient way to find an item from a sorted list. It works by repeatedly dividing the search interval in half. If the value of the search key is less than the middle item, the search continues in the lower half; if it's greater, the search continues in the upper half. This process continues until the value is found or the interval is empty. The binary search function returns the index of the target if found, otherwise -1.",
                "imports": "import sys",
                "code": "def binary_search(arr, target):\n    left, right = 0, len(arr) - 1\n    while left <= right:\n        mid = left + (right - left) // 2\n        if arr[mid] == target:\n            return mid\n        elif arr[mid] < target:\n            left = mid + 1\n        else:\n            right = mid - 1\n    return -1\n"
                "time_complexity": "O(log n)"
            }

            ```
        '''

    refinement_prompt = refinement_instruction_prompt.replace("{user_prompt}", user_prompt)
    refinement_prompt = refinement_prompt.replace("{previous_code}", previous_code)
    refinement_prompt = refinement_prompt.replace("{evaluation_feedback}", feedback_evaluator)

    debate_response = ""
    if strategy_debate == "0":
        debate_response += str(developers_debate(programmers, user_prompt, refinement_prompt, strategy_debate, max_rounds=MAXROUNDS_NO))
    elif strategy_debate == '1':
        debate_response += str(developers_debate(programmers, user_prompt, refinement_prompt, strategy_debate, max_rounds=MAXROUNDS_NO))
    else:
        debate_response += str(developers_debate_mixed_strategy(programmers, user_prompt, refinement_prompt, max_rounds=MAXROUNDS_NO))

    return debate_response


def do_instant_runoff_voting(programmers, debate_response, responses_allowed, readability_complexity, user_prompt):
    # Apply instant runoff voting to break disagreement
    winner = instant_runoff_voting(debate_response, responses_allowed.keys())

    if isinstance(winner, int):
        if winner in responses_allowed:
            print("Final decision through Instant Runoff Voting:")
            solution = responses_allowed[winner]
            print(solution)
            return solution

    elif isinstance(winner, list):
        print("Tie between the following candidates (Instant Runoff Voting):")
        for w in winner:
            print(f"Candidate {w}: {responses_allowed[w]}")
        return responses_allowed[winner[0]]  # Return one of the tied responses

    return None


def instant_runoff_voting(votes, valid_candidates):
    """
    votes: list of primary preferences (e.g., [1, 0, 2, 1]) from the agents.
    valid_candidates: set or list of valid candidate indices (with syntactically correct code).

    Returns:
        - a single winning candidate index (int), or
        - a list of tied candidates (list of int) if no clear winner.
    """
    from collections import Counter

    active_candidates = set(valid_candidates)

    while len(active_candidates) > 1:
        vote_count = Counter()

        # Count only the first valid vote per agent
        for vote in votes:
            if vote in active_candidates:
                vote_count[vote] += 1

        total_votes = sum(vote_count.values())

        # Check for absolute majority
        for candidate, count in vote_count.items():
            if count > total_votes / 2:
                return candidate

        # Eliminate candidate(s) with fewest votes
        if not vote_count:
            break  # No valid votes remain

        min_votes = min(vote_count.values())
        to_eliminate = [cand for cand, count in vote_count.items() if count == min_votes]

        if len(to_eliminate) == len(active_candidates):
            return list(active_candidates)  # Tie

        for cand in to_eliminate:
            active_candidates.remove(cand)

    return list(active_candidates) if len(active_candidates) > 1 else next(iter(active_candidates))






example_refined_debate_prompt = """
# Instruction
You are an expert source code evaluator. Your task is to analyze a list of the source code generated by AI models
and select the best one.
We will provide you with the user input (the original coding prompt) and a list of {AGENTS_NO} AI-generated code response.
You should first read the user input carefully to understand the coding task, and then select the best code 
response based on the **Evaluation** section below.

# Evaluation
## Metric Definition
Each code solution has:
    - an unique number between 0 and {_AGENTS_NO-1};
    - a time complexity expressed in Big-O notation;
    - a cognitive complexity. 

You will be assessing each code solution according the following aspects: time complexity and cognitive complexity.
The definition of each criteria is described in Criteria section.
According these criteria, you will generate an integer which is the unique number related to the best code solution. 
Prioritize solutions with lower time complexity first. If time complexities are equal, then prioritize lower cognitive complexity.
The instruction for the coding task is provided in the **User Input** section, while the list of code solutions 
is provided in the **AI-generated Responses** section.


## Criteria
- Time complexity: it measures how the execution time of the algorithm grows as the input size increases. 
Big-O notation is the standard for expressing time complexity. More lower it is (e.g., O(N) is better than O(N^2)), better the code solution is.
- Cognitive complexity: it quantifies the difficulty for a human to understand a piece of code or a function.
More lower it is (e.g., a flat structure is better than deeply nested loops), better the code solution is.

# Output Format
Return only a single integer which corresponds to the unique number of the best code solution choosen.
Your response must be a single integer with **no explanation**, **no text**, and **no punctuation**.
Responding with anything other than a number will be considered an error.


## Evaluation Steps
STEP 1: Analyze each code response in terms of time complexity and cognitive complexity.
STEP 2: Based on the defined criteria and prioritization in **Metric Definition** section, select the best code solution.
STEP 3: Provide your answer as described in **Output Format** section.


# User Input
{user_prompt}

## AI-generated Responses
{ai_responses}
"""

def get_formatted_responses(responses, cognitive_complexity, AGENTS_NO): #responses = JSON responses
    extracted_formatted_responses = {}
    extracted_time_complexity = {}

    formatted_responses = {}

    string = "\n------\n"

    keys = responses.keys()

    for i in keys:
        extracted_formatted_responses[i] = get_formatted_code_solution(responses[i])
        extracted_time_complexity[i] = extract_time_complexity(responses[i])

    for i in keys:
        formatted_responses[i] = (string + "SOLUTION: \n" + extracted_formatted_responses[i] +
                                  "\nUNIQUE NUMBER OF SOLUTION: " + str(i) +
                                  "\nTIME COMPLEXITY: " + extracted_time_complexity[i] +
                                  "\nCOGNITIVE COMPLEXITY: " + str(cognitive_complexity[i]))

    return formatted_responses

def get_refined_debate_prompt(AGENTS_NO, user_prompt, formatted_responses):

    prompt = example_refined_debate_prompt
    prompt = prompt.replace("{AGENTS_NO}", str(AGENTS_NO))
    prompt = prompt.replace("{_AGENTS_NO-1}", str(AGENTS_NO-1))
    prompt = prompt.replace("{user_prompt}", user_prompt)
    ai_responses = ""

    keys = formatted_responses.keys()
    for var in keys:
        ai_responses += formatted_responses[var]

    prompt = prompt.replace("{ai_responses}", ai_responses)

    return prompt

def get_refined_agreement(model, deb_prompt):
    messages = [{"role": "user", "content": deb_prompt}]
    response = model.respond({"messages": messages}, response_format=schema_feedback)
    return response.content