from datasets import load_dataset

# Load the BigCodeBench dataset in streaming mode.
# This allows you to iterate over the dataset without downloading the entire thing.
ds = load_dataset("bigcode/bigcodebench", streaming=True, split="v0.1.4")

# Initialize lists to store different fields from each sample
instruct_prompt_list = []
canonical_solution_list = []
test_list = []
libs_list = []

# Iterate over the first 10 samples in the dataset
for i, sample in enumerate(ds):
    if i == 10:
        break

    # Extract relevant fields from the current sample
    instruct_prompt = sample["instruct_prompt"]         # Instruction prompt for the task
    canonical_solution = sample["canonical_solution"]   # Ground-truth solution for the prompt
    code_prompt = sample["code_prompt"]                 # Initial code prompt (possibly incomplete)
    libs = sample["libs"]                               # List of required libraries
    test = sample["test"]                               # Unit tests for the task

    # Print the current sample's key fields for inspection
    print({
        "instruct_prompt": instruct_prompt,
        "canonical_solution": canonical_solution,
        "code_prompt": code_prompt,
        "libs": libs,
        "test": test
    })

    # Append extracted values to their respective lists
    instruct_prompt_list.append(instruct_prompt)
    canonical_solution_list.append(canonical_solution)
    test_list.append(test)
    libs_list.append(libs)


"""
ALTERNATIVE VERSION WITHOUT STREAMING

If you prefer to load the entire dataset into memory (non-streaming mode):

ds = load_dataset("bigcode/bigcodebench", split="v0.1.4")

# You can either convert the dataset to a DataFrame or iterate over it directly
for sample in ds:
    print({
        "instruct_prompt": sample["instruct_prompt"],
        "canonical_solution": sample["canonical_solution"],
        "code_prompt": sample["code_prompt"],
        "libs": sample["libs"]
    })
"""
