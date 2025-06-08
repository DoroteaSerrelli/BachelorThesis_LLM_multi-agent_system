"""
Utility functions to manage agents (initialization, response).
"""

from typing import Dict, Any
import lmstudio as lms

from utility_function import get_set_number_solutions
from metrics import extract_time_complexity
from response_JSON_schema import schema_complexity, schema_inputs, schema_feedback


# ======= FUNCTIONS FOR CREATING AND MANAGING AGENTS =======

def get_clone_agent(type_model, temperature=0.3):
    """
    Initialize a new LLM model instance (clone) with the specified temperature.

    Args:
        type_model: The type or path of the model to initialize.
        temperature: The temperature setting for sampling (default is 0.3).

    Returns:
        A new model instance.
    """
    model = lms.llm(type_model, config={"temperature": temperature})
    return model


def get_model_info(model):
    """
    Retrieve configuration and metadata information from the model.

    Args:
        model: The model instance.

    Returns:
        A dictionary containing model information.
    """
    return model.get_info()


def extract_identifier(data: Dict[str, Any]) -> str | None:
    """
    Extracts the value of the 'identifier' key from a dictionary.

    Args:
        data: The dictionary to extract the value from.

    Returns:
        The value associated with 'identifier' if it exists, otherwise None.
    """
    return data.get("identifier")


def get_programmer_first_response(model, problem_definition):
    """
    Get the initial model response to a code generation task defined in the user prompt.

    Args:
        model: The LLM agent.
        problem_definition: A string defining the problem to solve.

    Returns:
        The model's first response in the format defined by 'schema_complexity'.
    """
    messages = [{"role": "user", "content": problem_definition}]
    response = model.respond({"messages": messages}, response_format=schema_complexity)
    return response.content


def get_first_response_test_inputs(model, few_shot_prompt, user_prompt):
    """
    Get the initial model response including test inputs for the generated code.

    Args:
        model: The LLM agent.
        few_shot_prompt: Additional examples or instructions in the prompt.
        user_prompt: The actual code generation task.

    Returns:
        The model's response in 'schema_complexity' format, including test inputs.
    """
    system_prompt = (
        "You are an AI expert programmer that writes code "
        "or helps to review code for bugs, based on the user request. "
    )

    messages = [{"role": "user", "content": user_prompt},
                {"role": "system", "content": system_prompt + few_shot_prompt}]
    response = model.respond({"messages": messages}, response_format=schema_complexity)
    return response.content


def get_response(model, debate_response):
    """
    Provide a model response during an agent debate or discussion.

    Args:
        model: The LLM agent.
        debate_response: A prompt or statement provided by the user.

    Returns:
        The model's response following the 'schema_complexity' schema.
    """
    messages = [{"role": "user", "content": debate_response}]
    response = model.respond({"messages": messages}, response_format=schema_complexity)
    return response.content


def get_response_test_inputs(model, user_prompt, debate_response):
    """
    Provide a model response including test inputs, during an agent discussion.

    Args:
        model: The LLM agent.
        user_prompt: The original user task.
        debate_response: The ongoing discussion context.

    Returns:
        The model's response using the 'schema_inputs' format (includes test cases).
    """
    messages = [{"role": "user", "content": "User asks: " + user_prompt + "\n" + debate_response}]
    response = model.respond({"messages": messages}, response_format=schema_inputs)
    return response.content


# ======= FUNCTIONS FOR CREATING PROMPTS FOR AGENT DEBATES =======

def get_discussion_feedback_prompt_test_inputs(pers_response, pers_time, pers_cognitive,
                                               other_answers, readability_complexity,
                                               time_complexity, AGENTS_NO):
    """
    Generate a discussion prompt for agents to review and improve their responses based on others' solutions,
    including time and cognitive complexity scores.

    Args:
        pers_response: The agent's own initial response.
        pers_time: Time complexity score of the agent's response.
        pers_cognitive: Cognitive complexity score of the agent's response.
        other_answers: List of responses from other agents.
        readability_complexity: List of cognitive complexity scores from other agents.
        time_complexity: List of time complexity scores from other agents.
        AGENTS_NO: Total number of agents involved.

    Returns:
        A formatted string prompt for feedback discussion.
    """
    deb_prompt = (
        'These are the solutions to the code generation problem from other agents, which are included in ---: ')

    for i in range(0, AGENTS_NO - 1):
        deb_prompt += ('\n ONE AGENT SOLUTION: \n --- ' + other_answers[i] + '\n '
                       ' This solution has time complexity = ' + str(time_complexity[i]) +
                       ' and cognitive_complexity = ' + str(readability_complexity[i]) +
                       '--- ')

    deb_prompt += ("""\nUsing the solutions from other agents as additional advice, examine your answer, which is delimited by ---.
                      If you can improve your answer, which is included in ---, in terms of time complexity or cognitive complexity,
                      state your new answer at the start of your new response in the form **Yes**; otherwise, 
                      answer in the form **No**."""
                   '--- YOUR ANSWER:' + pers_response + ' '
                   ' Your answer has time_complexity= ' + str(pers_time) +
                   ' and cognitive_complexity = ' + str(pers_cognitive) + '---')

    return deb_prompt


def get_discussion_feedback_prompt(placeholder, pers_response, pers_cognitive,
                                   other_answers, readability_complexity, AGENTS_NO):
    """
    Generate a prompt for agent self-review based on the responses of a subset of other agents.

    Args:
        placeholder: Index placeholder to determine subset of agents.
        pers_response: The current agent's own response.
        pers_cognitive: Cognitive complexity of the current response.
        other_answers: List of other agents' responses.
        readability_complexity: List of cognitive complexities of those responses.
        AGENTS_NO: Total number of agents.

    Returns:
        A formatted debate prompt for feedback and refinement.
    """
    deb_prompt = (
        'These are the solutions to the code generation problem from other agents, which are included in ---: ')

    range_values = get_set_number_solutions(placeholder, AGENTS_NO)
    for i in range_values:
        deb_prompt += ('\n ONE AGENT SOLUTION: \n --- ' + other_answers[i] + '\n --- ' +
                       'This solution has time complexity = ' + extract_time_complexity(other_answers[i]) +
                       ' and cognitive_complexity = ' + str(readability_complexity[i]) + '--- ')

    deb_prompt += ("""\nUsing the solutions from other agents as additional advice, examine your answer, which is delimited by ---.
                      If you can improve your answer, which is included in ---, in terms of time complexity or cognitive complexity,
                      state your new answer at the start of your new response in the form **Yes**; otherwise, 
                      answer in the form **No**."""
                   '--- YOUR ANSWER:' + pers_response + ' '
                   ' Your answer has time_complexity= ' + extract_time_complexity(pers_response) +
                   ' and cognitive_complexity = ' + str(pers_cognitive) + '---')

    return deb_prompt


def get_self_refinement_prompt(pers_response, user_prompt, other_answers):
    """
    Create a prompt for self-refinement based on multiple agent responses.

    Args:
        pers_response: The agent's current answer (can be empty).
        user_prompt: The original code generation task.
        other_answers: Dictionary of other agents' responses.

    Returns:
        A prompt that encourages the agent to revise or generate a new solution.
    """
    deb_prompt = (
        f'''Here are several AI-generated solutions to the following code generation problem:

        -----
        CODE GENERATION TASK:
        {user_prompt}
        -----\n

        -----
        AI-GENERATED RESPONSES '''
    )

    for i in other_answers.keys():
        deb_prompt += f"\n**{i}.**\n---\n{other_answers[i]}\n---"
    deb_prompt += "-----\n"

    if pers_response != "":
        deb_prompt += (
            "\nConsidering the solutions listed in **AI-GENERATED RESPONSES** section, revise and improve your following answer: "
            "\n----- "
            "YOUR ANSWER "
            f"{pers_response}\n"
            "-----\n"
        )
    else:
        deb_prompt += (
            "\nConsidering the solutions listed in **AI-GENERATED RESPONSES** section as additional information, generate your solution to the code generation task."
        )

    return deb_prompt


def get_refined_debate_prompt(AGENTS_NO, user_prompt, formatted_responses):
    """
        Builds a comprehensive debate prompt tailored for a source code evaluator agent.

        It combines the user task with all AI-generated responses and their metrics
        (cognitive and time complexity) to enable comparative evaluation.

        Args:
            AGENTS_NO: Number of participating agents.
            user_prompt: Original code generation prompt.
            formatted_responses: Formatted string versions of each response.

        Returns:
            A fully constructed debate prompt string for evaluation.
        """

    refine_debate = """
    You are an expert source code evaluator. 

    We will provide you with the user input (the original coding prompt) and a list of {AGENTS_NO} AI-generated code responses 
    to the user input.
    Each code response has following attributes:
        - an unique number between 0 and {_AGENTS_NO-1}.
        - a time complexity expressed in Big-O notation: it measures how the execution time of the algorithm grows 
            as the input size increases. More lower it is (e.g., O(N) is better than O(N^2)), better the code solution is.
        - a cognitive complexity: it quantifies the difficulty for a human to understand a piece of code or a function.
            More lower it is (e.g., a flat structure is better than deeply nested loops), better the code solution is. 

    Your task is to analyze the list of the code solutions and select the best one following these steps:

    STEP 1: Read the user input carefully to understand the coding task.
    STEP 2: Analyze each code response in terms of time complexity and cognitive complexity.
    STEP 3: Select the best code solution in this way: 
            - prioritize solutions with lower time complexity first. 
            - if time complexities are equal, then prioritize lower cognitive complexity.
    STEP 4: Answer with only a single integer which corresponds to the unique number of the best code solution choosen.
            Your response must be a single integer with **no explanation**, **no text**, and **no punctuation**.
            Responding with anything other than a number will be considered an error.

     The instruction for the coding task is provided in the **User Input** section, while the list of code solutions 
    is provided in the **AI-generated Responses** section.


    # User Input
    {user_prompt}

    ## AI-generated Responses
    {ai_responses}
    """

    prompt = refine_debate
    prompt = prompt.replace("{AGENTS_NO}", str(AGENTS_NO))
    prompt = prompt.replace("{_AGENTS_NO-1}", str(AGENTS_NO-1))
    prompt = prompt.replace("{user_prompt}", user_prompt)
    ai_responses = ""

    keys = formatted_responses.keys()
    for var in keys:
        ai_responses += formatted_responses[var]

    prompt = prompt.replace("{ai_responses}", ai_responses)

    return prompt


def get_agreement(model, user_prompt, deb_prompt):
    """
    Ask the model to choose the best solution among the given ones or validate its own.

    Args:
        model: The LLM agent.
        user_prompt: Original problem statement.
        deb_prompt: Discussion prompt to guide the model's reasoning.

    Returns:
        The model's agreement response (no specific schema assumed).
    """
    messages = [{"role": "user", "content": "User has asked: " + user_prompt + "\n" + deb_prompt}]
    response = model.respond({"messages": messages})  # Optional: define a JSON schema for validation
    return response.content


def get_refined_agreement(model, deb_prompt):
    """
        Sends a debate prompt to an agent and retrieves its agreement (selected best solution).

        The response is expected in a specific schema format to extract structured feedback.

        Args:
            model: The LLM agent to query.
            deb_prompt: The constructed debate prompt with all necessary info.

        Returns:
            The agent’s structured feedback (selected solution index).
        """
    messages = [{"role": "user", "content": deb_prompt}]
    response = model.respond({"messages": messages}, response_format=schema_feedback)
    return response.content