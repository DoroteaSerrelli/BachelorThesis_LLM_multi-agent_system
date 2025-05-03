'''
    Utility functions to manage evaluator agent to score a solution.
'''

import lmstudio as lms

from response_JSON_schema import evaluation_schema
from evaluation_prompt import instruct_prompt

# Weights in percentage (total = 100)
CORRECTNESS_WEIGHT = 40
SECURITY_WEIGHT = 10
MAINTAINABILITY_WEIGHT = 10
RELIABILITY_WEIGHT = 10
COMPILE_ERR_WEIGHT = 15
EXEC_ERR_WEIGHT = 15

# Maximum number of errors before score reaches 0
MAX_ERRORS = 10


def get_evaluator(type_model):
    evaluator = lms.llm(type_model)
    return evaluator


def eval_code(user_prompt, ai_response, evaluator):
    """Evaluate the generated code against the prompt used."""
    prompt = instruct_prompt
    prompt = prompt.replace("{user_prompt}", user_prompt)
    prompt = prompt.replace("{ai_response}", ai_response)

    print("PROMPT PER LA VALUTAZIONE" + prompt)

    messages = [{"role": "user", "content": prompt}]
    response = evaluator.respond({"messages": messages}, response_format=evaluation_schema)
    return response.content


def extract_criteria_scores(json_evaluation):
    import json
    str_json = json.loads(json_evaluation)

    criteria_scores = {"Correctness": 0, "Security": 0, "Maintainability": 0, "Reliability": 0, "Compilation Errors": 0,
                       "Execution Errors": 0}

    criteria_scores["Correctness"] = int(str_json["Correctness"])
    criteria_scores["Security"] = int(str_json["Security"])
    criteria_scores["Maintainability"] = int(str_json["Maintainability"])
    criteria_scores["Reliability"] = int(str_json["Reliability"])
    criteria_scores["Compilation Errors"] = int(str_json["Compilation Errors"])
    criteria_scores["Execution Errors"] = int(str_json["Execution Errors"])

    return criteria_scores


def calculate_score_code(criteria_scores: dict):
    correctness = criteria_scores["Correctness"]
    security = criteria_scores["Security"]
    maintainability = criteria_scores["Maintainability"]
    reliability = criteria_scores["Reliability"]
    compilation_err = criteria_scores["Compilation Errors"]
    execution_err = criteria_scores["Execution Errors"]

    # Normalize error counts into 0–100 scores (the more errors, the lower the score)
    compilation_score = max(0, 100 - (100 * min(compilation_err, MAX_ERRORS) / MAX_ERRORS))
    execution_score = max(0, 100 - (100 * min(execution_err, MAX_ERRORS) / MAX_ERRORS))

    # Weighted average calculation
    weighted_avg = (
        CORRECTNESS_WEIGHT * correctness +
        SECURITY_WEIGHT * security +
        MAINTAINABILITY_WEIGHT * maintainability +
        RELIABILITY_WEIGHT * reliability +
        COMPILE_ERR_WEIGHT * compilation_score +
        EXEC_ERR_WEIGHT * execution_score
    ) / 100

    return weighted_avg
