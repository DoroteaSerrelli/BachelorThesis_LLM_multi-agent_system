'''
    Utility functions to manage agents (initialization, response).
'''

import lmstudio as lms
from response_JSON_schema import schema


# Inizializzare il modello (copie di una tipologia di modello)
def getCloneAgent(typeModel):
    model = lms.llm(typeModel, config={"temperature": 0.3})

    return model


# Costruzione del prompt per il dibattito tra modelli
# other_answers = list

def getDiscussionFeedbackPrompt(pers_response, other_answers):
    deb_prompt = (
        'These are the solutions to the code generation problem from other agents, which are included in ---: ')

    for i in other_answers:
        deb_prompt += ('\n ONE AGENT SOLUTION: \n --- ' + i + '\n --- ')

    deb_prompt += ("""\nUsing the solutions from other agents as additional advice, examine your answer, which is delimited by ---.
                        Can you improve your answer, which is included in ---, in terms of time complexity, functional correctness, or readability?
                        Make sure to state your answer in the form **Yes** or **No**, at the start of your response."""
                       '--- YOUR ANSWER:' + pers_response + ' ---')

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
    response = model.respond({"messages": messages}, response_format=schema)
    return response.content

def get_agreement(model, user_prompt, deb_prompt):

    messages = [{"role": "user", "content": "User has asked: " + user_prompt + "\n"+deb_prompt}]
    response = model.respond({"messages": messages}) #vedi se è necessario definire uno schema JSON per l'agreement
    return response.content


# Funzione per fornire una risposta del modello durante una discussione
def get_response(model, user_prompt, debate_response):
    messages = [{"role": "user", "content": "User asks: " + user_prompt + "\n" + debate_response}
                ]
    response = model.respond({"messages": messages}, response_format=schema)
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