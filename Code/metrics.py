''' This file contains functions related to metrics about code:
    - time complexity
    - readability
    used in main.py file during debate.
'''

'''Readability'''
import ast
import astunparse
from inspect import getsource
from cognitive_complexity.api import get_cognitive_complexity_for_node
from cognitive_complexity.utils.ast import has_recursive_calls, is_decorator, process_child_nodes, process_node_itself

def get_cognitive_complexity(func):
    func = func if isinstance(func, str) else getsource(func)
    funcdef = ast.parse(func).body[0]
    if is_decorator(funcdef):
        return get_cognitive_complexity(funcdef.body[0])

    details = []
    complexity = 0
    for node in funcdef.body:
        node_complexity = get_cognitive_complexity_for_node(node)
        complexity += node_complexity
        node_code = astunparse.unparse(node)
        if f"{funcdef.name}(" in node_code: # +1 for recursion
            node_complexity += 1
            complexity += 1
        details.append([node_complexity, node_code])
    details.append([complexity, "Total"])
    return complexity, details
