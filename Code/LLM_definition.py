'''
    Utility functions to manage agents (initialization, response).
'''

import lmstudio as lms

from Code.metrics import extract_time_complexity
from Code.response_JSON_schema import schema_complexity
from response_JSON_schema import schema
AGENTS_NO = 2


# Inizializzare il modello (copie di una tipologia di modello)
def getCloneAgent(typeModel):
    model = lms.llm(typeModel, config={"temperature": 0.3})

    return model


# Costruzione del prompt per il dibattito tra modelli
# other_answers = list

def getDiscussionFeedbackPrompt(pers_response, pers_cognitive, other_answers, readability_complexity):
    deb_prompt = (
        'These are the solutions to the code generation problem from other agents, which are included in ---: ')

    for i in range(0, AGENTS_NO-1):
        deb_prompt += ('\n ONE AGENT SOLUTION: \n --- ' + other_answers[i] + '\n --- ' +
                       'This solution has time complexity = ' + extract_time_complexity(other_answers[i]) +
                       ' and cognitive_complexity = ' + str(readability_complexity[i]) +
                       '--- '
                       )

    deb_prompt += ("""\nUsing the solutions from other agents as additional advice, examine your answer, which is delimited by ---.
                            If you can improve your answer, which is included in ---, in terms of time complexity or cognitive complexity,
                            state your new answer at the start of your new response in the form **Yes**; otherwise, 
                            answers in the form **No**."""
                   '--- YOUR ANSWER:' + pers_response + ' '
                   ' Your answer has time_complexity= ' + extract_time_complexity(pers_response) +
                   ' and cognitive_complexity = ' + str(pers_cognitive) + '---')

    return deb_prompt


def getDiscussionGivenAnswersFeedbackPrompt(placeholder, pers_response, pers_cognitive, other_answers, readability_complexity):
    deb_prompt = (
        'These are the solutions to the code generation problem from other agents, which are included in ---: ')

    for i in range(0, AGENTS_NO - 1):
        deb_prompt += ('\n AGENT SOLUTION **'+str(placeholder)+'** : \n --- ' + other_answers[i] + '\n --- ' +
                       'This solution has time complexity = ' + extract_time_complexity(other_answers[i]) +
                       ' and cognitive_complexity = ' + str(readability_complexity[i]) +
                       '--- '
                       )

    deb_prompt += (f"""\nUsing the solutions from other agents as additional advice, examine your answer, which is delimited by ---.
                                In terms of time complexity and cognitive complexity,
                                answers with {placeholder} if your answers is better than the responses of the other agents.
                                Otherwise, if the solution of another agent is better than yours, 
                                answers with the number of the solution. """
                   '--- YOUR ANSWER:' + pers_response + ' '
                   ' Your answer has time_complexity= ' + extract_time_complexity(pers_response) +
                   ' and cognitive_complexity = ' + str(pers_cognitive) + '---')

    return deb_prompt


def getDiscussionPrompt(pers_response, other_answers):
    deb_prompt = ('These are the solutions to the code generation problem from other agents, which are included in ---: ')

    for i in other_answers:
        deb_prompt += ('\n ONE AGENT SOLUTION: \n --- ' + i + '\n --- ')

    deb_prompt += ('\nUsing the solutions from other agents as additional advice, improve your answer, which is separated by --- .'
                   '--- YOUR ANSWER:' + pers_response + ' ---')

    return deb_prompt


# Funzione per ottenere la risposta del modello
def get_first_response(model, few_shot_prompt, user_prompt):
    # Definire il prompt di sistema
    system_prompt = (
        "You are an AI expert programmer that writes code "
        "or helps to review code for bugs, "
        "based on the user request. "
    )

    messages = [{"role": "user", "content": user_prompt},
                {"role": "system", "content": system_prompt+few_shot_prompt}
                ]
    response = model.respond({"messages": messages}, response_format=schema_complexity)
    return response.content

def get_agreement(model, user_prompt, deb_prompt):

    messages = [{"role": "user", "content": "User has asked: " + user_prompt + "\n"+deb_prompt}]
    response = model.respond({"messages": messages}) #vedi se è necessario definire uno schema JSON per l'agreement
    return response.content


# Funzione per fornire una risposta del modello durante una discussione
def get_response(model, user_prompt, debate_response):
    messages = [{"role": "user", "content": "User asks: " + user_prompt + "\n" + debate_response}
                ]
    response = model.respond({"messages": messages}, response_format=schema_complexity)
    return response.content


# Convert JSON schema response into a code response: imports+code

def get_response_to_evaluate(ai_response):
    """
    Estrae le stringhe 'imports' e 'code' da un dizionario.

    Args:
        data (dict): Un dizionario che contiene le chiavi 'imports' e 'code'.

    Returns:
        str: Una stringa che contiene il contenuto di 'imports' e 'code', concatenati con un separatore.
        None: Se 'imports' o 'code' non sono presenti nel dizionario.
    """
    if "imports" in ai_response and "code" in ai_response:
        imports = ai_response["imports"]
        code = ai_response["code"]
        return f"{imports}\n\n{code}"
    else:
        return None