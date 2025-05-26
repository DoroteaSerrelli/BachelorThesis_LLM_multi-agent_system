"""
    Helper functions to manage the debate between multiple LLM agents
    collaborating on a source code generation task.
    The debate process aims to iteratively refine and evaluate candidate solutions,
    based on cognitive (readability) and time complexity, until a consensus is reached.
"""
from debate_prompt_attempts import get_refined_debate_prompt, get_formatted_responses, get_refined_agreement, \
    get_multiple_choice_numbers_prompt, getDiscussionGivenAnswersFeedbackPrompt_NoComparing
# Imports
from LLM_definition import (
    get_programmer_first_response,
    get_discussion_given_answers_feedback_prompt,
    get_response,
    get_discussion_prompt_k_solutions,
    get_agreement,
    get_discussion_given_answers_feedback_prompt_no_comparing, get_clone_agent,
    get_model_info, extract_identifier, get_self_refinement_prompt
)
import json
from metrics import get_cognitive_complexity
from tabulate import tabulate
from utility_function import remove_duplicates, equals_cognitive_complexity, equals_time_complexity, \
    get_random_element, get_k_responses, get_feedback_value, count_tokens

# Number of LLM agents participating in the debate
AGENTS_NO = 3

# Maximum number of allowed debate rounds before falling back to majority voting
MAXROUNDS_NO = 5


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

def debate_with_self_refinement(user_prompt, few_shot_prompt, agents, max_rounds=MAXROUNDS_NO):
    """
        Simulates a multi-round debate among agents until consensus is reached or a fallback is triggered.

        Steps:
        1. Agents independently generate an initial response to a prompt.
        2. Each response is evaluated for readability using cognitive complexity metrics.
        3. Each agent reviews peer responses and provides feedback (votes for the best one).
        4. If no consensus is reached, agents refine their responses in subsequent rounds.
        5. After max rounds, majority voting is used to select the final answer.
    """

    # === Phase 1: Each model independently generates a first response ===

    response = []  # Stores responses from all agents
    for i in range(AGENTS_NO):
        response.append(get_programmer_first_response(agents[i], few_shot_prompt, user_prompt))

    # Display all initial responses
    for i in range(AGENTS_NO):
        print(f"Response model {i}: {response[i]}")

    # === Phase 2: Iterative debate rounds ===
    current_round = 1
    feedback = []
    feedback_allowed = []

    while current_round <= max_rounds:
        feedback_allowed.clear()

        # === Measure readability (cognitive complexity) of each response ===
        readability_complexity = []  # Stores total cognitive complexity for each response
        details_readability_complexity = []  # Stores node-level breakdown of complexity

        for i in range(AGENTS_NO):
            response_json = json.loads(response[i])  # Parse JSON response
            total, details = get_cognitive_complexity(response_json["code"])
            print(tabulate(details, headers=["Complexity", "Node"], tablefmt="fancy_grid"))
            readability_complexity.append(total)
            details_readability_complexity.append(details)

        # === Construct the prompt for each agent to analyze others' responses ===

        # Rimuovere le risposte con cognitive complexity pari a -1: errori sintattici

        counter = 0

        responses_allowed = {}  # le risposte che hanno cognitive complexity != -1
        readability_complexity_allowed = {} # i valori di cognitive complexity delle risposte che hanno cognitive complexity != -1

        for i in range(0, AGENTS_NO):
            if readability_complexity[i] != -1:
                counter += 1
                responses_allowed[i] = response[i]
                readability_complexity_allowed[i] = readability_complexity[i]

        # Formattazione per prompt di dibattito
        formatted_responses = get_formatted_responses(responses_allowed, readability_complexity_allowed, counter)
        debate_prompt = get_refined_debate_prompt(counter, user_prompt, formatted_responses)

        # === Collect feedback from each agent (which solution they prefer) ===

        for i in range(AGENTS_NO):
            feedback.append(get_feedback_value(get_refined_agreement(agents[i], debate_prompt)))

        print(f"\nRound {current_round} - Feedback")
        for i in range(0, AGENTS_NO):
            print(f"Feedback model {i}: {feedback[i]}\n")

        # Verify if feedback is an integer between 0 and AGENTS_NO-1

        for var in feedback:
            if 0 <= var < AGENTS_NO:
                feedback_allowed.append(var)


        # === Check if all agents agree on the same solution ===
        possible_solutions = set(feedback_allowed)  # Unique solutions selected by the agents

        if len(possible_solutions) == 0: # Tutte le risposte generate dai modelli sono sintatticamente errate
            return "-1" # Dibattito fallito

        if len(possible_solutions) == 1:
            print("Agreement")
            print("\nFinal answer:")
            solution = str()
            for var in possible_solutions:
                solution = response[int(var)]
                print(solution)
            return solution  # Return the agreed-upon solution


        # Print all proposed candidate solutions for transparency
        for var in feedback_allowed:
            print("Candidate solution: " + str(var))

        # === If disagreement persists, proceed with self-refinement strategy ===
        response = do_self_refinement(agents, response, readability_complexity, user_prompt)

        feedback.clear()

        current_round += 1

    # === If max rounds exceeded, apply majority voting to resolve ===
    vote_index = majority_voting(feedback_allowed)
    return response[int(vote_index)]


def debate_with_k_candidates(user_prompt, few_shot_prompt, agents, max_rounds=MAXROUNDS_NO):
    """
        Same as simulate_round(), but adds a strategy where agents debate over a smaller subset (k)
        of top candidate solutions when a deadlock occurs.

        - Promotes convergence by narrowing focus to fewer promising answers.
        - Self-refinement still applies if disagreement persists.
    """

    # === Phase 1: Each model independently generates a first response ===
    response = []  # Stores responses from all agents
    for i in range(AGENTS_NO):
        response.append(get_programmer_first_response(agents[i], few_shot_prompt, user_prompt))

    # Display all initial responses
    for i in range(AGENTS_NO):
        print(f"Response model {i}: {response[i]}")

    # === Phase 2: Iterative debate rounds ===
    current_round = 1
    feedback = []
    feedback_allowed = []

    while current_round <= max_rounds:
        feedback_allowed.clear()
        # === Measure readability (cognitive complexity) of each response ===
        readability_complexity = []  # Stores total cognitive complexity for each response
        details_readability_complexity = []  # Stores node-level breakdown of complexity
        import json

        for i in range(AGENTS_NO):
            response_json = json.loads(response[i])  # Parse JSON response
            total, details = get_cognitive_complexity(response_json["code"])
            print(tabulate(details, headers=["Complexity", "Node"], tablefmt="fancy_grid"))
            readability_complexity.append(total)
            details_readability_complexity.append(details)

        # === Construct the prompt for each agent to analyze others' responses ===
        debate_prompt = ""

        for i in range(AGENTS_NO):
            formatted_responses = get_formatted_responses(response, readability_complexity, AGENTS_NO)
            debate_prompt = get_refined_debate_prompt(AGENTS_NO, user_prompt, formatted_responses)
            print(f"Prompt token count for round {current_round}: {count_tokens(debate_prompt)}")

        for i in range(AGENTS_NO):
            feedback.append(get_feedback_value(get_refined_agreement(agents[i], debate_prompt)))

        print(f"\nRound {current_round} - Feedback")
        for i in range(0, AGENTS_NO):
            print(f"Feedback model {i}: {feedback[i]}\n")

        # Verify if feedback is an integer between 0 and AGENTS_NO-1

        for var in feedback:
            if 0 <= var < AGENTS_NO:
                feedback_allowed.append(var)

        # === Check if all agents agree on the same solution ===
        possible_solutions = set(feedback_allowed)  # Unique solutions selected by the agents

        if len(possible_solutions) == 1:
            print("Agreement")
            print("\nFinal answer:")
            solution = str()
            for var in possible_solutions:
                solution = response[int(var)]
                print(solution)
            return solution  # Return the agreed-upon solution

        if len(possible_solutions) == 0:
            for i in range(AGENTS_NO):
                response.append(get_programmer_first_response(agents[i], few_shot_prompt, user_prompt))

            # Display all initial responses
            for i in range(AGENTS_NO):
                print(f"Response model {i}: {response[i]}")
                current_round += 1
                continue

        # Print all proposed candidate solutions for transparency
        for var in feedback_allowed:
            print("Candidate solution: " + str(var))

        k_response = continue_debate_on_k_solutions(feedback_allowed, user_prompt, response, readability_complexity, agents)

        if len(k_response) == 1:
            print("Agreement")
            print("\nFinal answer:")
            solution = str()
            for var in k_response:
                solution = response[int(var)]
                print(solution)
            return solution  # Return the agreed-upon solution

        # === If disagreement persists, proceed with self-refinement strategy ===
        if len(k_response) == len(possible_solutions):
            response = do_self_refinement(agents, response, user_prompt)

        feedback.clear()

        current_round += 2

    # === If max rounds exceeded, apply majority voting to resolve ===
    vote_index = majority_voting(feedback_allowed)
    return response[int(vote_index)]



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


# === Debate over k candidate solutions ===
def continue_debate_on_k_solutions(k_candidates_chosen, user_prompt, responses, readability_complexity, agents):
    """
        Reduces the debate scope to a smaller set of k candidate solutions.

        Each agent analyzes and votes on the best among the reduced solution set.
        Used to resolve deadlock or improve convergence.
    """

    k_cognitive_complexity = {}

    for i in range(AGENTS_NO):
        # Temporarily replace agent responses with the k selected ones
        responses[i] = responses[int(k_candidates_chosen[i])]
        if i not in k_cognitive_complexity:  # keep track cognitive complexity of k solutions
            k_cognitive_complexity[i] = readability_complexity[i]

    # Remove duplicates
    responses = remove_duplicates(responses)
    k_cognitive_complexity = remove_duplicates(k_cognitive_complexity)

    # Build the prompt to analyze k-candidate solutions
    formatted_responses = get_formatted_responses(responses, k_cognitive_complexity, len(responses)) #AGENTS_NO = len(responses) perché considero k_candidates
    debate_prompt = get_refined_debate_prompt(AGENTS_NO, user_prompt, formatted_responses)
    print(f"Prompt token count on continue_debate_on_k_solutions: {count_tokens(debate_prompt)}")

    new_response = []

    for i in range(AGENTS_NO):
        # Agent generates a new opinion
        new_response.append(get_response(agents[i], user_prompt, debate_prompt))
        print(f"Improved model {i} response: {new_response[i]}")


    return new_response


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
    Extended version of the debate simulation.
    
    Features:
    - Uses feedback generation *without direct comparison* between solutions.
    - Introduces convergence check after 2 non-agreement rounds:
        - If all candidate solutions are equivalent in time and cognitive complexity,
          randomly selects one.
        - Otherwise, triggers self-refinement and continues debate.
    
    Used when comparison-based evaluation may bias or slow convergence.
'''

def simulate_complete_round(user_prompt, few_shot_prompt, agents, max_rounds=MAXROUNDS_NO):
    # === Phase 1: Each model independently generates a first response ===
    response = []  # Stores responses from all agents
    for i in range(AGENTS_NO):
        response.append(get_programmer_first_response(agents[i], few_shot_prompt, user_prompt))

    # Display all initial responses
    for i in range(AGENTS_NO):
        print(f"Response model {i}: {response[i]}")

    # === Phase 2: Iterative debate rounds ===
    current_round = 1
    not_agreement_rounds = 0    # numero di round in cui non ci è stata convergenza
    while current_round <= max_rounds:
        # === Measure readability (cognitive complexity) of each response ===
        readability_complexity = []  # Stores total cognitive complexity for each response
        details_readability_complexity = []  # Stores node-level breakdown of complexity
        import json

        for i in range(AGENTS_NO):
            response_json = json.loads(response[i])  # Parse JSON response
            total, details = get_cognitive_complexity(response_json["code"])
            print(tabulate(details, headers=["Complexity", "Node"], tablefmt="fancy_grid"))
            readability_complexity.append(total)
            details_readability_complexity.append(details)

        # === Construct the prompt for each agent to analyze others' responses ===
        debate_prompt = getDiscussionGivenAnswersFeedbackPrompt_NoComparing(response, user_prompt, readability_complexity, AGENTS_NO) # prova per non comparazione


        # === Collect feedback from each agent (which solution they prefer) ===
        feedback = []
        for i in range(AGENTS_NO):
            feedback.append(get_feedback_value(get_refined_agreement(agents[i], debate_prompt)))

        print(f"\nRound {current_round} - Feedback")
        for i in range(AGENTS_NO):
            print(f"Feedback model {i}: {feedback[i]}\n")

        # === Check if all agents agree on the same solution ===
        possible_solutions = set(feedback)  # Unique solutions selected by the agents

        if len(possible_solutions) == 1:
            print("Agreement")
            print("\nFinal answer:")
            solution = str()
            for var in possible_solutions:
                solution = response[int(var)]
                print(solution)
            return solution  # Return the agreed-upon solution

        not_agreement_rounds += 1
        # Print all proposed candidate solutions for transparency
        for var in feedback:
            print("Candidate solution: " + str(var))

        k_responses = []

        if not_agreement_rounds >= 2:
            # Verifico se tutte le soluzioni hanno uguale complessità di tempo e uguale complessità di leggibilità
            k_responses = get_k_responses(response, feedback)
            if equals_time_complexity(k_responses) and equals_cognitive_complexity(readability_complexity):
                solution = str(get_random_element(k_responses))
                print("Agreement between equivalent solution")
                print("\nFinal answer:")

                print(solution)
                return solution  # Return the agreed-upon solution
            else:   #oppure inserire un modello mediatore che estrae la migliore soluzione
                response = do_self_refinement(agents, response, user_prompt)
                not_agreement_rounds = 0


        k_response = continue_debate_on_k_solutions(k_responses, user_prompt, response, readability_complexity, agents)

        if len(k_response) == 1:
            print("Agreement")
            print("\nFinal answer:")
            solution = str()
            for var in k_response:
                solution = response[int(var)]
                print(solution)
            return solution  # Return the agreed-upon solution

        """# === If disagreement persists, proceed with self-refinement strategy ===
        if len(k_response) == len(possible_solutions):
            response = debate_self_refinement(agents, response, user_prompt)"""

        not_agreement_rounds += 1
        round += 1

    # === If max rounds exceeded, apply majority voting to resolve ===
    vote_index = majority_voting(feedback)
    return response[vote_index]


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
        debate_response = str(developers_debate(programmers, user_prompt, refinement_prompt, strategy_debate, max_rounds=MAXROUNDS_NO))
    elif strategy_debate == '1':
        debate_response = str(developers_debate(programmers, user_prompt, refinement_prompt, strategy_debate, max_rounds=MAXROUNDS_NO))
    else:
        debate_response = str(simulate_complete_round(refinement_prompt, few_shot_prompt, programmers, max_rounds=MAXROUNDS_NO)) #<======= DA MODIFICARE L'ORDINE DEI PRIMI DUE PARAMETRI

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
