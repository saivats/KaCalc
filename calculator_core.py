import math
import operator


# --- Public API ---

def evaluate_expression(expression: str) -> str:
    """
    Evaluates a mathematical expression string and returns the result
    as a formatted string.

    This is the main public function for the calculator core.
    """
    try:
        # 1. Tokenize: Break the string into meaningful pieces
        tokens = _tokenize(expression)

        # 2. Shunting-Yard: Convert infix tokens to postfix (RPN)
        postfix_tokens = _shunting_yard(tokens)

        # 3. RPN Evaluation: Calculate the result from postfix tokens
        result = _evaluate_rpn(postfix_tokens)

        # Format the result nicely (remove .0 from integers)
        if result == int(result):
            return str(int(result))
        else:
            # Round to a reasonable number of decimal places
            return str(round(result, 10))

    except (ValueError, ZeroDivisionError, TypeError) as e:
        # Catch all math-related errors and return an error message
        return f"Error: {str(e)}"
    except Exception as e:
        # Catch unexpected errors (like mismatched parentheses)
        return f"Error: Malformed expression"


# --- 1. Tokenizer ---

def _tokenize(expression: str) -> list[str]:
    """Converts the expression string into a list of tokens."""
    tokens = []
    current_token = ""

    # Add whitespace around parentheses to make splitting easier
    expression = expression.replace("(", " ( ").replace(")", " ) ")

    # Handle implicit multiplication for parentheses, e.g., 5(3) -> 5*(3)
    expression = expression.replace(")(", ") * (")
    # e.g., 5sin(3) -> 5*sin(3)
    for func in _FUNCTIONS.keys():
        expression = expression.replace(f"{func}(", f"{func} (")
        expression = expression.replace(f"){func}", f") * {func}")

    lex_pass = expression.split()

    for i, part in enumerate(lex_pass):
        if _is_number(part):
            # Handle implicit multiplication e.g., 5( or 5pi
            if i > 0 and (lex_pass[i - 1] == ")" or lex_pass[i - 1] in _CONSTANTS):
                tokens.append("*")
            tokens.append(part)
        elif part in _OPERATORS or part in _FUNCTIONS or part in _CONSTANTS or part in "()":
            # Handle implicit multiplication e.g., pi( or (5)3
            if part == "(" and i > 0 and (_is_number(lex_pass[i - 1]) or lex_pass[i - 1] == ")"):
                tokens.append("*")

            tokens.append(part)

            if part == ")" and i + 1 < len(lex_pass) and _is_number(lex_pass[i + 1]):
                tokens.append("*")
        else:
            raise ValueError(f"Unknown token: {part}")

    return tokens


# --- 2. Shunting-Yard Algorithm (Infix to Postfix) ---

def _shunting_yard(tokens: list[str]) -> list[str]:
    """Converts a token list from infix to postfix (RPN) notation."""
    output_queue = []
    operator_stack = []

    for token in tokens:
        if _is_number(token):
            output_queue.append(token)
        elif token in _CONSTANTS:
            output_queue.append(token)
        elif token in _FUNCTIONS:
            operator_stack.append(token)
        elif token in _OPERATORS:
            # Handle operator precedence and associativity
            while (operator_stack and
                   operator_stack[-1] in _OPERATORS and
                   _PRECEDENCE[operator_stack[-1]] >= _PRECEDENCE[token]):
                output_queue.append(operator_stack.pop())
            operator_stack.append(token)
        elif token == "(":
            operator_stack.append(token)
        elif token == ")":
            # Pop operators until a matching '(' is found
            while operator_stack and operator_stack[-1] != "(":
                output_queue.append(operator_stack.pop())
            if not operator_stack or operator_stack[-1] != "(":
                raise ValueError("Mismatched parentheses")
            operator_stack.pop()  # Discard the '('

            # If a function is at the top, move it to output
            if operator_stack and operator_stack[-1] in _FUNCTIONS:
                output_queue.append(operator_stack.pop())

    # Pop remaining operators from the stack to the output
    while operator_stack:
        token = operator_stack.pop()
        if token == "(":
            raise ValueError("Mismatched parentheses")
        output_queue.append(token)

    return output_queue


# --- 3. RPN Evaluator ---

def _evaluate_rpn(tokens: list[str]) -> float:
    """Evaluates a postfix (RPN) token list."""
    stack = []

    for token in tokens:
        if _is_number(token):
            stack.append(float(token))
        elif token in _CONSTANTS:
            stack.append(_CONSTANTS[token])
        elif token in _FUNCTIONS:
            if not stack:
                raise ValueError(f"Not enough arguments for {token}")
            # Functions take one argument
            arg = stack.pop()
            stack.append(_FUNCTIONS[token](arg))
        elif token in _OPERATORS:
            if len(stack) < 2:
                raise ValueError(f"Not enough arguments for {token}")
            # Operators take two arguments
            num2 = stack.pop()
            num1 = stack.pop()
            stack.append(_OPERATORS[token](num1, num2))

    if len(stack) != 1:
        raise ValueError("Invalid expression")

    return stack[0]


# --- Helper Definitions ---

def _is_number(s: str) -> bool:
    """Checks if a string can be converted to a float."""
    try:
        float(s)
        return True
    except ValueError:
        return False


# Operator definitions
_OPERATORS = {
    "+": operator.add,
    "-": operator.sub,
    "*": operator.mul,
    "/": operator.truediv,
    "^": operator.pow,
}

# Operator precedence
_PRECEDENCE = {
    "+": 1,
    "-": 1,
    "*": 2,
    "/": 2,
    "^": 3,
}

# Function definitions (using Python's math module)
_FUNCTIONS = {
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "asin": math.asin,
    "acos": math.acos,
    "atan": math.atan,
    "sqrt": math.sqrt,
    "log": math.log10,  # log base 10
    "ln": math.log,  # natural log (base e)
    "rad": math.radians,  # convert degrees to radians
    "deg": math.degrees,  # convert radians to degrees
}

# Constant definitions
_CONSTANTS = {
    "pi": math.pi,
    "e": math.e,
}

# --- Test Harness (to run this file directly) ---

if __name__ == "__main__":
    """
    This block runs ONLY when you execute this file directly.
    It's a great way to test that your code works.
    """
    print("--- Calculator Core Test ---")

    test_expressions = [
        "5 + 3",
        "5 * 3 + 2",
        "5 * (3 + 2)",
        "10 / 2 - 3",
        "2^3",
        "sqrt(9)",
        "sin(rad(90))",
        "pi * 2",
        "5(3 + 1)",  # Implicit multiplication
        "pi(2)",
        "5sin(rad(90))",  # Implicit multiplication
        "10 / 0",  # Error test
        "5 +",  # Error test
        "(5 + 3",  # Error test
    ]

    for expr in test_expressions:
        result = evaluate_expression(expr)
        print(f"Expr: '{expr}'  ->  Result: {result}")

    print("\n--- Interactive Test ---")
    print("Enter 'exit' to quit.")
    while True:
        try:
            expression = input("Enter expression: ")
            if expression.lower() == 'exit':
                break
            print("Result:", evaluate_expression(expression))
        except EOFError:
            break
