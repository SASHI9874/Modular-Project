import ast
import operator
import math

# Safe operators
SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
}

# Safe functions
SAFE_FUNCTIONS = {
    'abs': abs,
    'round': round,
    'min': min,
    'max': max,
    'sqrt': math.sqrt,
    'pow': pow,
    'sin': math.sin,
    'cos': math.cos,
    'tan': math.tan,
}


def safe_eval(expression: str) -> float:
    """Safely evaluate mathematical expression"""
    
    def eval_node(node):
        if isinstance(node, ast.Constant):
            return node.n
        elif isinstance(node, ast.BinOp):
            op = SAFE_OPERATORS.get(type(node.op))
            if not op:
                raise ValueError(f"Unsupported operator: {type(node.op).__name__}")
            left = eval_node(node.left)
            right = eval_node(node.right)
            return op(left, right)
        elif isinstance(node, ast.UnaryOp):
            op = SAFE_OPERATORS.get(type(node.op))
            if not op:
                raise ValueError(f"Unsupported operator: {type(node.op).__name__}")
            return op(eval_node(node.operand))
        elif isinstance(node, ast.Call):
            func_name = node.func.id
            func = SAFE_FUNCTIONS.get(func_name)
            if not func:
                raise ValueError(f"Unsupported function: {func_name}")
            args = [eval_node(arg) for arg in node.args]
            return func(*args)
        else:
            raise ValueError(f"Unsupported expression type: {type(node).__name__}")
    
    try:
        tree = ast.parse(expression, mode='eval')
        return eval_node(tree.body)
    except Exception as e:
        raise ValueError(f"Invalid expression: {str(e)}")


def calculate(expression: str) -> dict:
    """
    Calculate mathematical expression
    
    Args:
        expression: Math expression as string
        
    Returns:
        dict with result and original expression
    """
    print(f"🧮 [Calculator] Evaluating: {expression}")
    
    try:
        result = safe_eval(expression)
        
        print(f"✅ [Calculator] Result: {result}")
        
        return {
            "result": result,
            "expression": expression,
            "success": True
        }
    
    except Exception as e:
        print(f"❌ [Calculator] Error: {str(e)}")
        
        return {
            "result": None,
            "expression": expression,
            "error": str(e),
            "success": False
        }