from datasets import load_dataset

# Carica il dataset in modalità streaming (opzionale, utile per dataset molto grandi)
ds = load_dataset("bigcode/bigcodebench", streaming=True, split="v0.1.4")

# Estrai solo le colonne desiderate
for sample in ds:
    instruct_prompt = sample["instruct_prompt"]
    canonical_solution = sample["canonical_solution"]
    code_prompt = sample["code_prompt"]
    libs = sample["libs"]

    print({
        "instruct_prompt": instruct_prompt,
        "canonical_solution": canonical_solution,
        "code_prompt": code_prompt,
        "libs": libs
    })




"""VARIANTE SENZA STREAMING 

ds = load_dataset("bigcode/bigcodebench", split="v0.1.4")

# Puoi convertire in DataFrame o iterare normalmente
for sample in ds:
    print({
        "instruct_prompt": sample["instruct_prompt"],
        "canonical_solution": sample["canonical_solution"],
        "code_prompt": sample["code_prompt"],
        "libs": sample["libs"]
    })

"""