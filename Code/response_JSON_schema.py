# A JSON schema for code generation task

"""Schema for code solutions to to_do about code generation."""

schema = {
    "type": "object",
    "properties": {
        "documentation": {
            "type": "string",
            "description": "Description of the problem and approach"
        },
        "imports": {
            "type": "string",
            "description": "Code block import statements"
        },
        "code": {
            "type": "string",
            "description": "Code block not including import statements"
        }
    },
    "required": ["documentation", "imports", "code"]
}


"""Schema for evaluation task about AI-generated code."""

evaluation_schema = {
"type": "object",
    "properties": {
        "score": {
            "type": "string",
            "description": "the score from 1 to 5 for each criteria related to the code: Correctness, Security, Maintainability, Reliability, Compilation Errors, Execution Errors."
        },
        "evaluation": {
            "type": "string",
            "description": "The overall evaluation of the code response according to the rating rubric: Very good, Good, Ok, Bad, Very bad."
        },
        "explanation": {
            "type": "string",
            "description": "A detailed explanations for your assessment, including specific examples of issues and the error counts."
        }
    },
    "required": ["documentation", "imports", "code"]
}