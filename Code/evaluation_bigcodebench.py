from datasets import load_dataset

# Carica il dataset in modalità streaming
ds = load_dataset("bigcode/bigcodebench", streaming=True, split="v0.1.4")

instruct_prompt_list = []
canonical_solution_list = []

# Itera sulle prime 10 righe
for i, sample in enumerate(ds):
    if i == 10:
        break
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


    instruct_prompt_list.append(instruct_prompt)
    canonical_solution_list.append(canonical_solution)


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