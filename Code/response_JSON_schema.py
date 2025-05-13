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

"""Schema for code solutions to to_do about code generation within Big-O complexity."""

schema_complexity = {
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
        },
        "time_complexity": {
            "type": "string",
            "description": "Time complexity of the code block not including import statements, expressed in Big-O notation"
        }
    },
    "required": ["documentation", "imports", "code", "time_complexity"]
}

"""Schema for code solutions to to_do about code generation, including example input tests."""

schema_inputs = {
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
        },
        "test_inputs": {
            "type": "array",
            "description": "List of input examples to test the code with",
            "items": {
                "type": "object",
                "properties": {
                    "args": {
                        "type": "array",
                        "description": "Positional arguments to pass to the function"
                    },
                    "kwargs": {
                        "type": "object",
                        "description": "Keyword arguments to pass to the function (optional)"
                    }
                },
                "required": ["args"],
                "additionalProperties": False
            }
        }
    },
    "required": ["documentation", "imports", "code", "test_inputs"]
}


"""Schema for evaluation task about AI-generated code."""

evaluation_schema = {
    "type": "object",
    "properties": {
        "Correctness": {
            "type": "integer",
            "description": "The score from 0 to 100 about the correctness of the AI-generated code."
        },
        "Security": {
            "type": "integer",
            "description": "The score from 0 to 100 about the security of the AI-generated code."
        },
        "Maintainability": {
            "type": "integer",
            "description": "The score from 0 to 100 about the maintainability of the AI-generated code."
        },
        "Reliability": {
            "type": "integer",
            "description": "The score from 0 to 100 about the reliability of the AI-generated code."
        },
        "Compilation Errors": {
            "type": "integer",
            "description": "The number of compilation errors affected by the AI-generated code."
        },
        "Execution Errors": {
            "type": "integer",
            "description": "The number of execution errors affected by the AI-generated code."
        },
        "Explanation": {
            "type": "string",
            "description": "A detailed explanation for your assessment, including specific examples of issues and the error counts."
        }
    },
    "required": [
        "Correctness", "Security", "Maintainability", "Reliability",
        "Compilation Errors", "Execution Errors", "Explanation"
    ]
}