"""
    Utility functions to manage agents (initialization, response).
"""
from typing import Dict, Any

import lmstudio as lms

from utility_function import get_set_number_solutions
from metrics import extract_time_complexity
from response_JSON_schema import schema_complexity, schema_inputs


### ======= FUNZIONI LEGATE ALLA CREAZIONE E GESTIONE DEGLI AGENTI =======

# Inizializzare il modello (copie di una tipologia di modello)
def get_clone_agent(type_model, temperature=0.3):
    model = lms.llm(type_model, config={"temperature": temperature})

    return model

# Ottenere informazioni sui parametri e le caratteristiche dell'agente
def get_model_info(model):
    return model.get_info()


# Estrarre il modello LLM dell'agente
def extract_identifier(data: Dict[str, Any]) -> str | None:
    """
    Estrae il valore della chiave "identifier" da un dizionario.

    Args:
        data: Il dizionario da cui estrarre il valore.

    Returns:
        Il valore della chiave "identifier" se presente, altrimenti None.
    """
    return data.get("identifier")


# Funzione per ottenere la risposta iniziale del modello al task di generazione del codice sorgente definito nell'user prompt
def get_first_response(model, few_shot_prompt, user_prompt):
    # Definire il prompt di sistema
    system_prompt = (
        "You are an AI expert programmer that writes code "
        "or helps to review code for bugs, "
        "based on the user request. "
    )

    messages = [{"role": "user", "content": user_prompt},
                {"role": "system", "content": system_prompt + few_shot_prompt}
                ]
    response = model.respond({"messages": messages}, response_format=schema_complexity)
    return response.content


# Funzione per ottenere la risposta iniziale del modello al task di generazione del codice sorgente definito nell'user
# prompt, insieme ai test inputs per il codice fornito
def get_first_response_test_inputs(model, few_shot_prompt, user_prompt):
    # Definire il prompt di sistema
    system_prompt = (
        "You are an AI expert programmer that writes code "
        "or helps to review code for bugs, "
        "based on the user request. "
    )

    messages = [{"role": "user", "content": user_prompt},
                {"role": "system", "content": system_prompt + few_shot_prompt}
                ]
    response = model.respond({"messages": messages}, response_format=schema_complexity)
    return response.content


### ======= FUNZIONI LEGATE ALLA CREAZIONE DEL PROMPT DI DIBATTITO TRA GLI AGENTI =======

def get_discussion_feedback_prompt_test_inputs(pers_response, pers_time, pers_cognitive, other_answers,
                                            readability_complexity, time_complexity, AGENTS_NO):
    deb_prompt = (
        'These are the solutions to the code generation problem from other agents, which are included in ---: ')

    for i in range(0, AGENTS_NO - 1):
        deb_prompt += ('\n ONE AGENT SOLUTION: \n --- ' + other_answers[i] + '\n '
                                                                             ' This solution has time complexity = ' + str(
            time_complexity[i]) +
                       ' and cognitive_complexity = ' + str(readability_complexity[i]) +
                       '--- ')

    deb_prompt += ("""\nUsing the solutions from other agents as additional advice, examine your answer, which is delimited by ---.
                        If you can improve your answer, which is included in ---, in terms of time complexity or cognitive complexity,
                        state your new answer at the start of your new response in the form **Yes**; otherwise, 
                        answers in the form **No**."""
                   '--- YOUR ANSWER:' + pers_response + ' '
                                                        ' Your answer has time_complexity= ' + str(pers_time) +
                   ' and cognitive_complexity = ' + str(pers_cognitive) + '---')

    return deb_prompt


# other_answers = list

def get_discussion_given_answers_feedback_prompt(placeholder, pers_response, pers_cognitive, other_answers,
                                            others_readability_complexity, AGENTS_NO):
    deb_prompt = (
            'Here are some solutions to the code generation problem given by other agents, which are included in ---.'
            'Each solution has:'
            '* an unique number between 0 and ' + str(AGENTS_NO - 1) + ';'
                                                                       '* a time complexity defined in Big-O notation;'
                                                                       '* a cognitive complexity.'
    )

    other_solutions_numbers = get_set_number_solutions(placeholder, AGENTS_NO-1)

    for i in other_solutions_numbers:
        index = int(i)
        if other_answers[index] != "":
            deb_prompt += ('\n SOLUTION NUMBER ' + str(index) + ' : \n --- ' + other_answers[index] + '\n ' +
                           '* Time complexity = ' + extract_time_complexity(other_answers[index]) +
                           '* Cognitive complexity = ' + str(others_readability_complexity[index]) +
                           '--- '
                           )

    # If agent gives no answer (cognitive complexity = -1)
    if pers_response != "":
        deb_prompt += (f'--- YOUR ANSWER NUMBER ' + str(placeholder) + ' : \n ---' + pers_response + '\n ' +
                       '* Time complexity= ' + extract_time_complexity(pers_response) +
                       '* Cognitive complexity = ' + str(pers_cognitive) + '---')

        deb_prompt += (f"""\nUsing the solutions from other agents as additional advice, examine your answer, which is defined in the section '--- YOUR ANSWER NUMBER {placeholder}'.
                                Now, your task is to choose the best solution in terms of both time and cognitive complexity.
                                Your response must be one of the following ways:
                                - **only** the number corresponding to the agent solution choosen if that answer is better than yours.
                                - **only** the number {placeholder} if your answer is better than the responses of the other agents.

                                Your response must be a **single integer** with **no explanation**, **no text**, and **no punctuation**.
                                Responding with anything other than a number will be considered an error."""
                       )

    else:

        deb_prompt += (f"""\nUsing the solutions from other agents as additional advice, choose the best solution in terms of both time and cognitive complexity.
                        Your response must be **only** the number corresponding to the agent solution choosen.
                        Your response must be a **single integer** with **no explanation**, **no text**, and **no punctuation**.
                        Responding with anything other than a number will be considered an error."""
                       )

    return deb_prompt


def get_discussion_prompt_k_solutions(responses, k_cognitive_complexity, AGENTS_NO):

    deb_prompt = (
            'Here are the solutions to the code generation problem chosen in the previous round by other agents, which are included in ---.'
            'Each solution has:'
            '* an unique number between 0 and ' + str(AGENTS_NO - 1) + ';'
                                                                       '* a time complexity defined in Big-O notation;'
                                                                       '* a cognitive complexity.'
    )

    for i in range(0, AGENTS_NO):

        if (responses[i] != ""):
            deb_prompt += ('\n SOLUTION NUMBER ' + str(i) + ' : \n --- ' + responses[i] + '\n ' +
                           '* Time complexity = ' + extract_time_complexity(responses[i]) +
                           '* Cognitive complexity = ' + str(k_cognitive_complexity[i]) +
                           '--- '
                           )

    deb_prompt += (f"""\nUsing the solutions from other agents as additional advice, choose the best solution in terms of both time and cognitive complexity.
                            Your response must be **only** the number corresponding to the agent solution choosen.
                            Your response must be a **single integer** with **no explanation**, **no text**, and **no punctuation**.
                            Responding with anything other than a number will be considered an error."""
                   )

    return deb_prompt


def get_discussion_prompt(pers_response, other_answers):
    deb_prompt = (
        'Here are the solutions to the code generation problem provided by other agents:\n'
    )

    for i, answer in enumerate(other_answers):
        deb_prompt += (f"\n--- SOLUTION FROM AGENT {i + 1} ---\n{answer}\n--- END OF SOLUTION ---\n")

    if pers_response != "":
        deb_prompt += (
            "\n--- YOUR INITIAL ANSWER ---\n"
            f"{pers_response}\n"
            "--- END OF YOUR INITIAL ANSWER ---\n"
            "\nConsidering the solutions from other agents, revise and improve your initial answer."
        )
    else:
        deb_prompt += (
            "\nConsidering the solutions from other agents, generate your best solution to the code generation problem."
        )

    return deb_prompt




def get_agreement(model, user_prompt, deb_prompt):
    messages = [{"role": "user", "content": "User has asked: " + user_prompt + "\n" + deb_prompt}]
    response = model.respond({"messages": messages})  #vedi se è necessario definire uno schema JSON per l'agreement
    return response.content


# Funzione per fornire una risposta del modello durante una discussione
def get_response(model, user_prompt, debate_response):
    messages = [{"role": "user", "content": "User asks: " + user_prompt + "\n" + debate_response}
                ]
    response = model.respond({"messages": messages}, response_format=schema_complexity)
    return response.content


# Funzione per fornire una risposta del modello durante una discussione
def get_response_test_inputs(model, user_prompt, debate_response):
    messages = [{"role": "user", "content": "User asks: " + user_prompt + "\n" + debate_response}
                ]
    response = model.respond({"messages": messages}, response_format=schema_inputs)
    return response.content



#------------------------

def get_discussion_given_answers_feedback_prompt_no_comparing(answers, readability_complexity, AGENTS_NO):
    deb_prompt = (
            'Here are some solutions to the code generation problem given, which are included in ---.'
            'Each solution has:'
            '* an unique number between 0 and ' + str(AGENTS_NO - 1) + ';'
                                                                       '* a time complexity defined in Big-O notation;'
                                                                       '* a cognitive complexity.'
    )


    for i in range(0, AGENTS_NO):
        if (answers[i] != ""):
            deb_prompt += ('\n SOLUTION NUMBER ' + str(i) + ' : \n --- ' + answers[i] + '\n ' +
                           '* Time complexity = ' + extract_time_complexity(answers[i]) +
                           '* Cognitive complexity = ' + str(readability_complexity[i]) +
                           '--- '
                           )

    deb_prompt += (f"""\nNow, your task is to choose the best solution in terms of both time and cognitive complexity.
                            Your response must be **only** the number corresponding to the agent solution choosen.
                            Your response must be a **single integer** with **no explanation**, **no text**, and **no punctuation**.
                            Responding with anything other than a number will be considered an error."""
                       )

    return deb_prompt


#-----------------------------

def get_discussion_feedback_prompt(placeholder, pers_response, pers_cognitive, other_answers, readability_complexity):
        deb_prompt = (

            'These are the solutions to the code generation problem from other agents, which are included in ---: ')

        range_values = get_set_number_solutions(placeholder)
        for i in range_values:
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


                                                            ' Your answer has time_complexity= ' + extract_time_complexity(

            pers_response) +

                       ' and cognitive_complexity = ' + str(pers_cognitive) + '---')

        return deb_prompt