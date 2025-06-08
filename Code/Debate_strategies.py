"""
    Helper functions to manage the debate between multiple LLM agents
    collaborating on a source code generation task.
    The debate process aims to iteratively refine and evaluate candidate solutions,
    based on cognitive (readability) and time complexity, until a consensus is reached.
"""
import json

from tabulate import tabulate
from LLM_definition import (
    get_programmer_first_response,
    get_response,
    get_self_refinement_prompt, get_refined_agreement, get_refined_debate_prompt
)

from metrics import get_cognitive_complexity
from utility_function import equals_cognitive_complexity, equals_time_complexity, \
    get_random_element, get_k_responses, get_feedback_value, get_formatted_responses

# Number of LLM agents participating in the debate
AGENTS_NO = 2

# Maximum number of allowed debate rounds before falling back to majority voting
MAXROUNDS_NO = 4


def developers_debate(programmers, user_prompt, programmer_prompt, strategy_chosen, max_rounds=MAXROUNDS_NO):
    """
    Coordinates a structured debate among multiple AI agents (programmers) to collaboratively generate and refine
    source code in response to a user prompt.

    The function supports multiple rounds of discussion and two strategies (self-refinement or instant runoff voting)
    for resolving disagreements until convergence or max rounds are reached.

    Args:
        programmers: List of LLM agents acting as programmers.
        user_prompt: Original coding task prompt provided by the user.
        programmer_prompt: Template for initial model prompt with placeholder for user input.
        strategy_chosen: Debate strategy ('0' for self-refinement, '1' for instant runoff voting).
        max_rounds: Maximum number of debate rounds allowed.

    Returns:
        The final code solution as a string, or "-1" if no valid solution was reached.
    """

    problem_definition = programmer_prompt.replace("{user_prompt}", user_prompt)
    responses = []

    for programmer in programmers:
        responses.append(get_programmer_first_response(programmer, problem_definition))

    # Display all initial responses
    i = 0
    for response in responses:
        print(f"Response developer {i}: {response}")
        i += 1

    responses_allowed = {}  # contains responses with cognitive_complexity != -1
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

        counter = 0

        responses_allowed.clear()
        readability_complexity_allowed = {}  # contains cognitive_complexity != -1 related to the responses

        for i in range(0, AGENTS_NO):
            if readability_complexity[i] != -1:
                counter += 1
                responses_allowed[i] = responses[i]
                readability_complexity_allowed[i] = readability_complexity[i]

        # ====== Construct debate prompt ========

        formatted_responses = get_formatted_responses(responses_allowed, readability_complexity_allowed)
        debate_prompt = get_refined_debate_prompt(counter, user_prompt, formatted_responses)

        print("DEBATE_PROMPT OBTAINED: " + debate_prompt)

        # === Collect feedback from each agent (which solution they prefer) ===
        debate_response = []
        for i in range(AGENTS_NO):
            debate_response.append(get_feedback_value(get_refined_agreement(programmers[i], debate_prompt)))

        # Print responses
        print(f"\nRound {current_round} - Voting")
        for i in range(0, AGENTS_NO):
            print(f"Feedback model {i}: {debate_response[i]}\n")

        # All agents have chosen the same solution
        possible_solutions = set(debate_response)  # Unique solutions selected by the agents

        if len(possible_solutions) == 0:  # All responses have syntax errors
            return "-1"  # End debate with failure

        if len(possible_solutions) == 1:
            for var in possible_solutions:
                if 0 <= var < AGENTS_NO:
                    print("Agreement")
                    print("\nFinal answer:")

                    solution = responses[int(var)]
                    print(solution)
                    return solution  # Return the agreed-upon solution
                print("VOTING ERROR FOR SOLUTION NUMBER " + str(var))

        if strategy_chosen == "0":
            # SELF-REFINEMENT
            responses = do_self_refinement(programmers, responses, readability_complexity, user_prompt)
            debate_response.clear()
            readability_complexity.clear()
            details_readability_complexity.clear()

            i = 0
            for response in responses:
                print(f"Response self-refined developer {i}: {response}")
                i += 1

        if strategy_chosen == "1":
            # INSTANT RUNOFF VOTING
            response = do_instant_runoff_voting(debate_response, responses_allowed)
            print(f"Response instant_runoff_voting : {response}")
            return response

        current_round += 1

    # === If max rounds exceeded, apply majority voting to resolve ===
    vote_index = majority_voting(responses_allowed)
    return responses[int(vote_index)]


def developers_debate_mixed_strategy(programmers, user_prompt, programmer_prompt, max_rounds=MAXROUNDS_NO):
    """
    Executes a multi-agent debate process with a mixed strategy that dynamically switches
    between self-refinement and instant runoff voting based on agreement and complexity metrics.

    If disagreement persists after a few rounds, the function checks for equivalence in solutions
    using both time and cognitive complexity before resolving via voting.

    Args:
        programmers: List of LLM agents acting as programmers.
        user_prompt: The user-defined coding prompt.
        programmer_prompt: Prompt template used to initialize agents.
        max_rounds: Max number of debate iterations allowed.

    Returns:
        The final agreed-upon or selected code solution.
    """

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
    responses_allowed = {}  # contains responses with cognitive_complexity != -1
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

        counter = 0

        responses_allowed.clear()
        readability_complexity_allowed = {}  # contains cognitive_complexity != -1 related to the allowed solution

        for i in range(0, AGENTS_NO):
            if readability_complexity[i] != -1:
                counter += 1
                responses_allowed[i] = responses[i]
                readability_complexity_allowed[i] = readability_complexity[i]

        # ====== Construct debate prompt ========

        formatted_responses = get_formatted_responses(responses_allowed, readability_complexity_allowed)
        debate_prompt = get_refined_debate_prompt(counter, user_prompt, formatted_responses)

        print("# ============= DEBATE_PROMPT OBTAINED =================\n" + debate_prompt)

        # === Collect feedback from each agent (which solution they prefer) ===
        debate_response = []
        for i in range(AGENTS_NO):
            debate_response.append(get_feedback_value(get_refined_agreement(programmers[i], debate_prompt)))

        # Print responses
        print(f"\nRound {current_round} - Voting")
        for i in range(0, AGENTS_NO):
            print(f"Feedback model {i}: {debate_response[i]}\n")

        # All agents have chosen the same solution
        possible_solutions = set(debate_response)  # Unique solutions selected by the agents

        if len(possible_solutions) == 0:  # All responses have syntax errors
            return "-1"  # End debate with failure

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
            # All solutions have same time complexity and cognitive complexity
            k_responses = get_k_responses(responses, debate_response)
            k_readability_complexity = {}

            # Insert keys

            for index in k_responses:
                if index not in k_readability_complexity:
                    k_readability_complexity[int(index)] = 0

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
                # INSTANT RUNOFF VOTING
                response = do_instant_runoff_voting(debate_response, responses_allowed)
                return response

        else:
            # SELF-REFINEMENT
            responses = do_self_refinement(programmers, responses, readability_complexity, user_prompt)
            debate_response.clear()
            readability_complexity.clear()
            details_readability_complexity.clear()

            i = 0
            for response in responses:
                print(f"Response self-refined developer {i}: {response}")
                i += 1

        current_round += 1

        # === If max rounds exceeded, apply majority voting to resolve ===
    vote_index = majority_voting(responses_allowed)
    return responses[int(vote_index)]


# === Self-refinement ===

def do_self_refinement(agents, responses, readability_complexity, user_prompt):
    """
    Allows each agent to refine its own initial solution based on the responses of other agents,
    facilitating convergence through improvement.

    Agents receive others' valid solutions and attempt to generate a new, improved response.

    Args:
        agents: List of LLM agent instances.
        responses: Current code responses from each agent.
        readability_complexity: Cognitive complexity values of current responses.
        user_prompt: Original coding prompt provided by the user.

    Returns:
        A list of refined code responses.
    """

    debate_prompts = [None] * AGENTS_NO

    for i in range(AGENTS_NO):
        # Provide each agent with all other responses except its own
        other_responses = [r for j, r in enumerate(responses) if j != i]

        # Remove responses with cognitive_complexity= -1 because they contain syntax errore

        other_responses_allowed = {}  # contains answers with cognitive_complexity != -1

        for i in range(0, AGENTS_NO-1):
            if readability_complexity[i] != -1:
                other_responses_allowed[i] = other_responses[i]

        # Construct the prompt to trigger self-refinement

        if readability_complexity[i] != -1:
            debate_prompts[i] = get_self_refinement_prompt(responses[i], user_prompt, other_responses_allowed)
            print(f"SELF_REFINEMENT DEBATE PER AGENTE {i}: {debate_prompts[i]}")
            responses[i] = get_response(agents[i], debate_prompts[i])
        else:  # no answer given
            debate_prompts[i] = get_self_refinement_prompt("", user_prompt, other_responses_allowed)
            print(f"SELF_REFINEMENT DEBATE PER AGENTE {i}: {debate_prompts[i]}")
            responses[i] = get_response(agents[i], debate_prompts[i])

        # Generate improved response
        print(f"Improved model {i} response: {responses[i]}")

    return responses


# === Fallback: Majority Voting ===

def majority_voting(feedback):
    """
    Performs a fallback resolution strategy based on majority voting.

    If no convergence is reached during the debate, this function selects the solution
    with the most votes. Returns -1 in case of tie or invalid inputs.

    Args:
        feedback: Dictionary of agent vote responses.

    Returns:
        Index of the most voted solution or "-1" if a tie or invalid input occurs.
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


def after_evaluation_debate(user_prompt, feedback_evaluator, previous_code, programmers, strategy_debate):
    """
        Starts a post-evaluation debate process among agents to improve a previously generated solution.

        Combines the original prompt, the evaluator's feedback, and the prior code to prompt agents
        to refine the solution according to correctness, time, and cognitive complexity.

        Args:
            user_prompt: The original code generation task.
            feedback_evaluator: Feedback text from an external evaluator.
            previous_code: The code previously generated that needs refinement.
            programmers: List of LLM agents for refinement debate.
            strategy_debate: Strategy to apply (standard, mixed, or specific voting mechanism).

        Returns:
            The final refined solution after the debate process.
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


# === INSTANT RUNOFF VOTING ===
def do_instant_runoff_voting(debate_response, responses_allowed):
    """
        Resolves disagreement among agents using instant runoff voting (IRV).

        If no consensus is reached during debates, IRV ranks and eliminates the least preferred
        solutions in rounds until a winner emerges or a tie is declared.

        Args:
            debate_response: List of votes from agents for preferred solutions.
            responses_allowed: Dictionary of syntactically valid solutions.

        Returns:
            The winning solution string, or one randomly selected in case of a tie.
        """
    import random
    winner = instant_runoff_voting(debate_response, responses_allowed.keys())

    if isinstance(winner, int):
        if winner in responses_allowed:
            print("Final decision through Instant Runoff Voting:")
            solution = responses_allowed[winner]
            print(solution)
            return solution

    elif isinstance(winner, list):  # Tie
        print("Tie between the following candidates (Instant Runoff Voting):")
        for w in winner:
            print(f"Candidate {w}: {responses_allowed[w]}")

        # Choose randomly a candidate
        chosen = random.choice(winner)
        print(f"Randomly selected winner: Candidate {chosen}")
        return responses_allowed[chosen]

    return None


def instant_runoff_voting(votes, valid_candidates):
    """
    Executes the instant runoff voting algorithm to select a winner among candidates.

    Candidates are progressively eliminated based on least votes until one with
    majority is found or a tie remains.

    Args:
        votes: List of agents’ primary vote indices.
        valid_candidates: List or set of indices corresponding to valid solutions.

    Returns:
        The winning candidate index, or list of tied candidates if no majority is found.
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
