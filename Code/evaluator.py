'''
    Utility functions to manage evaluator agent to score a solution.
'''

import lmstudio as lms

from response_JSON_schema import evaluation_schema
from evaluation_prompt import instruct_prompt


def get_evaluator(type_model):
    evaluator = lms.llm(type_model)
    return evaluator


def eval_code(user_prompt, ai_response, evaluator):
    """Evaluate the generated code against the prompt used."""
    prompt = instruct_prompt
    prompt = prompt.replace("{user_prompt}", user_prompt)
    prompt = prompt.replace("{ai_response}", ai_response)

    messages = [{"role": "user", "content": prompt}]
    response = evaluator.respond({"messages": messages}, response_format=evaluation_schema)
    return response.content




