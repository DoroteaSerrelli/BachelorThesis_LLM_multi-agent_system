'''Example of evaluator usage'''

from LLM_definition import get_formatted_code_solution
from evaluator import get_evaluator, eval_code


eval = get_evaluator("codellama-7b-instruct")
print(eval_code("Write a Python function to calculate the sum of two numbers.", "def sum(a, b): \n return a + b", eval))

schema = {
    "code": "public static String getDate() { return new SimpleDateFormat(\"yyyy-MM-dd\").format(new Date()); }",
    "documentation": "The method returns the current date in the format yyyy-mm-dd.",
    "imports": "import java.text.SimpleDateFormat;"
}
print(get_formatted_code_solution(schema))