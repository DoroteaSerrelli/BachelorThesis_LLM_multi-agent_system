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
    get_first_response,
    get_discussion_given_answers_feedback_prompt,
    get_discussion_prompt,
    get_response,
    get_discussion_prompt_k_solutions,
    get_agreement,
    get_discussion_given_answers_feedback_prompt_no_comparing, get_clone_agent,
    get_model_info, extract_identifier
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
        response.append(get_first_response(agents[i], few_shot_prompt, user_prompt))

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
        #debate_prompts = []
        debate_prompt = ""
        for i in range(AGENTS_NO):
            '''# Exclude agent's own response and complexity
            other_responses = [r for j, r in enumerate(response) if j != i]
            other_readability_compl = [r for j, r in enumerate(readability_complexity) if j != i]
            # Build a custom prompt for that agent to evaluate others' responses
            debate_prompts.append(
                get_discussion_given_answers_feedback_prompt(
                    i, response[i], readability_complexity[i], other_responses, other_readability_compl, AGENTS_NO
                )
            )'''
            formatted_responses = get_formatted_responses(response, readability_complexity, AGENTS_NO)
            debate_prompt = get_refined_debate_prompt(AGENTS_NO, user_prompt, formatted_responses)
            print(f"Prompt token count for round {current_round}: {count_tokens(debate_prompt)}")


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
                response.append(get_first_response(agents[i], few_shot_prompt, user_prompt))

            # Display all initial responses
            for i in range(AGENTS_NO):
                print(f"Response model {i}: {response[i]}")
                current_round += 1
                continue

        # Print all proposed candidate solutions for transparency
        for var in feedback_allowed:
            print("Candidate solution: " + str(var))

        # === If disagreement persists, proceed with self-refinement strategy ===
        response = debate_self_refinement(agents, response, user_prompt)

        feedback.clear()

        current_round += 1

    # === If max rounds exceeded, apply majority voting to resolve ===
    vote_index = majority_voting(AGENTS_NO, feedback_allowed)
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
        response.append(get_first_response(agents[i], few_shot_prompt, user_prompt))

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
        #debate_prompts = []
        debate_prompt = ""

        for i in range(AGENTS_NO):
            # Exclude agent's own response and complexity
            other_responses = [r for j, r in enumerate(response) if j != i]
            other_readability_compl = [r for j, r in enumerate(readability_complexity) if j != i]
            # Build a custom prompt for that agent to evaluate others' responses
            '''debate_prompts.append(
                getDiscussionGivenAnswersFeedbackPrompt(
                    i, response[i], readability_complexity[i], other_responses, other_readability_compl, AGENTS_NO
                )
            )'''  # quello usato
            # quello da provare
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
                response.append(get_first_response(agents[i], few_shot_prompt, user_prompt))

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
            response = debate_self_refinement(agents, response, user_prompt)

        feedback.clear()

        current_round += 2

    # === If max rounds exceeded, apply majority voting to resolve ===
    vote_index = majority_voting(AGENTS_NO, feedback_allowed)
    return response[int(vote_index)]



# === Self-refinement ===

def debate_self_refinement(agents, responses, user_prompt):
    """
        Allows each agent to refine its own response based on the others' answers.

        This is used when agents disagree, encouraging evolution of solutions toward consensus.
    """

    debate_prompts = [None] * AGENTS_NO

    for i in range(AGENTS_NO):
        # Provide each agent with all other responses except its own
        other_responses = [r for j, r in enumerate(responses) if j != i]
        # Construct the prompt to trigger self-refinement

        if responses[i] != "":
            debate_prompts[i] = get_discussion_prompt(responses[i], other_responses)
            responses[i] = get_response(agents[i], user_prompt, debate_prompts[i])
        else:# se ha dato nessuna risposta
            increase_temp = 0.5 #aumento la temperatura
            info_model = get_model_info(agents[i])
            typeModel = extract_identifier(info_model)
            agents[i] = get_clone_agent(typeModel, increase_temp)
            responses[i] = get_first_response(agents[i], "", user_prompt)

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
def majority_voting(AGENTS_NO, feedback):
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
        response.append(get_first_response(agents[i], few_shot_prompt, user_prompt))

    # Display all initial responses
    for i in range(AGENTS_NO):
        print(f"Response model {i}: {response[i]}")

    # === Phase 2: Iterative debate rounds ===
    round = 1
    not_agreement_rounds = 0    # numero di round in cui non ci è stata convergenza
    while round <= max_rounds:
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

        print(f"\nRound {round} - Feedback:")
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
                response = debate_self_refinement(agents, response, user_prompt)
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
    vote_index = majority_voting(AGENTS_NO, feedback)
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

def after_evaluation_debate(user_prompt, few_shot_prompt, feedback_evaluator, previous_code, agents, strategy_debate, max_rounds=MAXROUNDS_NO):
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
                "code": "def binary_search(arr, target):\n    left, right = 0, len(arr) - 1\n    while left <= right:\n        mid = left + (right - left) // 2\n        if arr[mid] == target:\n            return mid\n        elif arr[mid] < target:\n            left = mid + 1\n        else:\n            right = mid - 1\n    return -1\n\n# Example usage\narr = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]\ntarget = 7\nresult = binary_search(arr, target)\nif result != -1:\n    print(f'Element found at index {result}')\nelse:\n    print('Element not found')"
                "time_complexity": "O(log n)"
            }

            ```
        '''

    refinement_prompt = refinement_instruction_prompt.replace("{user_prompt}", user_prompt)
    refinement_prompt = refinement_prompt.replace("{previous_code}", previous_code)
    refinement_prompt = refinement_prompt.replace("{evaluation_feedback}", feedback_evaluator)

    print("STO IN AFTER_EVALUATION: REFINEMENT_PROMOT: " + refinement_prompt)

    debate_response = ""
    if strategy_debate == "0":
        debate_response = str(debate_with_self_refinement(user_prompt, refinement_prompt, agents, max_rounds=MAXROUNDS_NO))
    elif strategy_debate == '1':
        debate_response = str(debate_with_k_candidates(user_prompt, refinement_prompt, agents, max_rounds=MAXROUNDS_NO))
    else:
        debate_response = str(simulate_complete_round(refinement_prompt, few_shot_prompt, agents, max_rounds=MAXROUNDS_NO)) #<======= DA MODIFICARE L'ORDINE DEI PRIMI DUE PARAMETRI

    return debate_response
