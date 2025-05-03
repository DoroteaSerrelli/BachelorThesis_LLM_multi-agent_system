''' Helper functions to manage the debate '''

# Number of agents involved in the debate
AGENTS_NO = 2

# Maximum number of rounds allowed before fallback to majority voting
MAXROUNDS_NO = 5

# Imports
from LLM_definition import (
    get_first_response,
    getDiscussionGivenAnswersFeedbackPrompt,
    getDiscussionPrompt,
    get_response,
    getDiscussionPromptKSolutions,
    get_agreement
)
from metrics import get_cognitive_complexity
from tabulate import tabulate

''' 
    This function simulates a debate between `n` agents over a code-generation task.

    - Each agent initially generates a solution to the user prompt independently.
    - Their responses are then evaluated based on time complexity and cognitive complexity (readability).
    - Each agent is then asked to choose the best solution from the group.

    If there is no consensus on a single best solution, several strategies may be applied:
    1. Each agent performs a self-refinement step, generating a new version of their code.
    2. Agents may compare the top-k candidate responses and vote again.
    ...
    
    If after `max_rounds` no agreement is reached, the system falls back to **majority voting**.
    In the case of a tie, the debate ends in failure.
'''


def simulate_round(user_prompt, few_shot_prompt, agents, max_rounds):
    # === Phase 1: Each model independently generates a first response ===
    response = []  # Stores responses from all agents
    for i in range(AGENTS_NO):
        response.append(get_first_response(agents[i], few_shot_prompt, user_prompt))

    # Display all initial responses
    for i in range(AGENTS_NO):
        print(f"Response model {i}: {response[i]}")

    # === Phase 2: Iterative debate rounds ===
    round = 1
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
        debate_prompts = []

        for i in range(AGENTS_NO):
            # Exclude agent's own response and complexity
            other_responses = [r for j, r in enumerate(response) if j != i]
            other_readability_compl = [r for j, r in enumerate(readability_complexity) if j != i]
            # Build a custom prompt for that agent to evaluate others' responses
            debate_prompts.append(
                getDiscussionGivenAnswersFeedbackPrompt(
                    i, response[i], readability_complexity[i], other_responses, other_readability_compl
                )
            )

        # === Collect feedback from each agent (which solution they prefer) ===
        feedback = []
        for i in range(AGENTS_NO):
            feedback.append(get_agreement(agents[i], user_prompt, debate_prompts[i]))

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

        # Print all proposed candidate solutions for transparency
        for var in feedback:
            print("Candidate solution: " + str(var))

        # === If disagreement persists, proceed with self-refinement strategy ===
        response = debate_self_refinement(agents, response, user_prompt)

        round += 1

    # === If max rounds exceeded, apply majority voting to resolve ===
    return majority_voting(AGENTS_NO, feedback)


# === Strategy 1: Self-refinement ===
# Each agent is prompted to improve its original response based on others' responses.
def debate_self_refinement(agents, responses, user_prompt):
    debate_prompts = [None] * AGENTS_NO

    for i in range(AGENTS_NO):
        # Provide each agent with all other responses except its own
        other_responses = [r for j, r in enumerate(responses) if j != i]
        # Construct the prompt to trigger self-refinement
        debate_prompts[i] = getDiscussionPrompt(responses[i], other_responses)
        # Generate improved response
        responses[i] = get_response(agents[i], user_prompt, debate_prompts[i])
        print(f"Improved model {i} response: {responses[i]}")

    return responses


# === Strategy 2: Debate over k candidate solutions ===
# Each agent is presented with a selection of top-k responses and must choose the best one.
def debate_on_k_solutions(k_candidates_chosen, user_prompt, responses, agents):
    for i in range(AGENTS_NO):
        # Temporarily replace agent responses with the k selected ones
        responses[i] = k_candidates_chosen[i]

    debate_prompts = [None] * AGENTS_NO

    for i in range(AGENTS_NO):
        # Provide each agent with all other responses except its own
        other_responses = [r for j, r in enumerate(responses) if j != i]
        # Build the prompt to analyze k-candidate solutions
        debate_prompts[i] = getDiscussionPromptKSolutions(responses[i], other_responses)
        # Agent generates a new opinion
        responses[i] = get_response(agents[i], user_prompt, debate_prompts[i])
        print(f"Improved model {i} response: {responses[i]}")

    return responses


# === Fallback: Majority Voting ===
# When no consensus is reached within the allowed rounds, fallback to vote counting.
def majority_voting(AGENTS_NO, feedback):
    ''' Perform majority voting among agent preferences '''
    schedule = [0] * AGENTS_NO

    # Count votes for each solution index
    for i in range(AGENTS_NO):
        for var in feedback:
            if int(var) == i:
                schedule[i] += 1

    max_votes = max(schedule)

    # Check if there is a tie for the most votes
    equal_votes = 0
    for var in schedule:
        if var == max_votes:
            equal_votes += 1

    if equal_votes != 1:
        # Tie detected — no clear majority
        return -1
    else:
        # Return the index of the most-voted solution
        for i, var in enumerate(schedule):
            if var == max_votes:
                return i