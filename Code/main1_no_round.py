import lmstudio as lms

# Definisci il prompt dell'utente
user_prompt = "Come cucinare la paella?"

# Inizializza i due modelli LLaMA
model_1 = lms.llm('llama-3.2-3b-instruct')
model_2 = lms.llm('llama-3.2-3b-instruct')

# Prepara la struttura del messaggio per entrambi i modelli
messages = [
    {"role": "user", "content": user_prompt}
]

# Ottieni la risposta dal primo modello
response_1 = model_1.respond({"messages": messages})
print("Risposta LLaMA 1:")
print(response_1.content)

# Ottieni la risposta dal secondo modello
response_2 = model_2.respond({"messages": messages})
print("\nRisposta LLaMA 2:")
print(response_2.content)
