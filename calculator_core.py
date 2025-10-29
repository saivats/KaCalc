import math

# --- Constants ---
# Token types
NUMBER = 'NUMBER'
OPERATOR = 'OPERATOR'
PARENTHESIS = 'PARENTHESIS'
IDENTIFIER = 'IDENTIFIER'
EOF = 'EOF'  # End of File

# --- BUG FIX: Define operator lists for main.py to use ---
BASIC_OPERATORS = ['+', '-', '*', '/']
FUNCTIONS = ['sqrt', 'sin', 'cos', 'tan', 'log', 'ln']


# --- Token ---
class TOKEN:
    def __init__(self, type, value):
        self.type = type
        self.value = value

    def __repr__(self):
        return f"TOKEN({self.type}, {repr(self.value)})"


# --- Lexer (Tokenizer) ---
# Takes a string ("5+3") and splits it into tokens ([TOKEN(NUMBER, 5), ...])
class Lexer:
    def __init__(self, text):
        self.text = text
        self.pos = 0
        self.current_char = self.text[self.pos] if self.pos < len(self.text) else None

    def advance(self):
        """Move the 'pos' pointer and update 'current_char'."""
        self.pos += 1
        self.current_char = self.text[self.pos] if self.pos < len(self.text) else None

    def skip_whitespace(self):
        while self.current_char is not None and self.current_char.isspace():
            self.advance()

    def get_number(self):
        """Return a (multi-digit) integer or float."""
        result = ''
        while self.current_char is not None and (self.current_char.isdigit() or self.current_char == '.'):
            result += self.current_char
            self.advance()
        try:
            return float(result) if '.' in result else int(result)
        except ValueError:
            raise LexerError(f"Invalid number format: {result}")

    def get_identifier(self):
        """Return an identifier (e.g., function name, constant)."""
        result = ''
        while self.current_char is not None and (self.current_char.isalnum() or self.current_char == '_'):
            result += self.current_char
            self.advance()
        return result

    def get_next_token(self):
        """Lexical analyzer (also known as scanner or tokenizer)."""
        while self.current_char is not None:
            if self.current_char.isspace():
                self.skip_whitespace()
                continue

            if self.current_char.isdigit():
                return TOKEN(NUMBER, self.get_number())

            if self.current_char.isalpha():
                return TOKEN(IDENTIFIER, self.get_identifier())

            # Check for ** BEFORE *
            if self.current_char == '*':
                if self.pos + 1 < len(self.text) and self.text[self.pos + 1] == '*':
                    self.advance()  # Consume the first *
                    self.advance()  # Consume the second *
                    return TOKEN(OPERATOR, '**')
                # It's just a regular multiplication
                self.advance()
                return TOKEN(OPERATOR, '*')

            # Check for other operators or parentheses
            if self.current_char in BASIC_OPERATORS:
                op = self.current_char
                self.advance()
                return TOKEN(OPERATOR, op)

            if self.current_char in ['(', ')']:
                op = self.current_char
                self.advance()
                return TOKEN(PARENTHESIS, op)

            raise LexerError(f"Invalid character: '{self.current_char}'")

        return TOKEN(EOF, None)


# --- Parser (Syntax Analyzer) ---
class ASTNode:
    pass


class BinOp(ASTNode):
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right


class UnaryOp(ASTNode):
    def __init__(self, op, operand):
        self.op = op
        self.operand = operand


class FuncCall(ASTNode):
    def __init__(self, func_name, argument):
        self.func_name = func_name
        self.argument = argument


class Num(ASTNode):
    def __init__(self, value):
        self.value = value


class Parser:
    def __init__(self, lexer):
        self.lexer = lexer
        self.current_token = self.lexer.get_next_token()
        self.operators = {
            '+': 1, '-': 1,
            '*': 2, '/': 2,
            '**': 3  # Precedence for **
        }

    def eat(self, token_type, token_value=None):
        if self.current_token.type == token_type and \
                (token_value is None or self.current_token.value == token_value):
            self.current_token = self.lexer.get_next_token()
        else:
            raise ParserError(f"Invalid syntax. Expected {token_type}" +
                              (f" with value {token_value}" if token_value else "") +
                              f", got {self.current_token}")

    def factor(self):
        """
        factor : (PLUS | MINUS) factor | NUMBER | LPAREN expr RPAREN | IDENTIFIER (LPAREN expr RPAREN)?
        """
        token = self.current_token

        if token.type == OPERATOR and token.value == '+':
            self.eat(OPERATOR, '+')
            return UnaryOp('+', self.factor())
        elif token.type == OPERATOR and token.value == '-':
            self.eat(OPERATOR, '-')
            return UnaryOp('-', self.factor())

        if token.type == NUMBER:
            self.eat(NUMBER)
            return Num(token.value)

        if token.type == PARENTHESIS and token.value == '(':
            self.eat(PARENTHESIS, '(')
            node = self.expr()
            self.eat(PARENTHESIS, ')')
            return node

        if token.type == IDENTIFIER:
            func_name = token.value
            self.eat(IDENTIFIER)
            if self.current_token.type == PARENTHESIS and self.current_token.value == '(':
                # It's a function call
                if func_name not in FUNCTIONS:
                    raise ParserError(f"Unknown function: {func_name}")
                self.eat(PARENTHESIS, '(')
                argument = self.expr()
                self.eat(PARENTHESIS, ')')
                return FuncCall(func_name, argument)
            else:
                # It's a constant
                if func_name == 'pi': return Num(math.pi)
                if func_name == 'e': return Num(math.e)
                raise ParserError(f"Unknown constant: {func_name}")

        raise ParserError(f"Unexpected token: {token}")

    def power(self):
        """ Handles exponentiation (**). This is right-associative. """
        node = self.factor()
        if self.current_token.type == OPERATOR and self.current_token.value == '**':
            token = self.current_token
            self.eat(OPERATOR, '**')
            node = BinOp(left=node, op=token.value, right=self.power())
        return node

    def term(self):
        """ Handles * and / """
        node = self.power()
        while self.current_token.type == OPERATOR and self.current_token.value in ('*', '/'):
            token = self.current_token
            self.eat(OPERATOR, token.value)
            node = BinOp(left=node, op=token.value, right=self.power())
        return node

    def expr(self):
        """ Handles + and - """
        node = self.term()
        while self.current_token.type == OPERATOR and self.current_token.value in ('+', '-'):
            token = self.current_token
            self.eat(OPERATOR, token.value)
            node = BinOp(left=node, op=token.value, right=self.term())
        return node

    def parse(self):
        """Entry point for the parser."""
        node = self.expr()
        if self.current_token.type != EOF:
            raise ParserError(f"Unexpected token after expression: {self.current_token}")
        return node


# --- Interpreter ---
class Interpreter:
    def __init__(self, parser):
        self.parser = parser
        self.functions = {
            'sqrt': math.sqrt,
            'sin': math.sin,
            'cos': math.cos,
            'tan': math.tan,
            'log': math.log10,
            'ln': math.log,
        }

    def visit(self, node):
        method_name = f'visit_{type(node).__name__}'
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        raise InterpreterError(f"No visit_{type(node).__name__} method")

    def visit_Num(self, node):
        return node.value

    def visit_UnaryOp(self, node):
        value = self.visit(node.operand)
        if node.op == '+':
            return +value
        elif node.op == '-':
            return -value

    def visit_FuncCall(self, node):
        func = self.functions.get(node.func_name)
        if not func:
            raise InterpreterError(f"Unknown function: {node.func_name}")

        argument_val = self.visit(node.argument)

        if node.func_name == 'sqrt' and argument_val < 0:
            raise InterpreterError("Domain error: sqrt of negative number")
        if node.func_name in ['log', 'ln'] and argument_val <= 0:
            raise InterpreterError("Domain error: log of non-positive number")

        return func(argument_val)

    def visit_BinOp(self, node):
        left_val = self.visit(node.left)
        right_val = self.visit(node.right)

        if node.op == '+':
            return left_val + right_val
        elif node.op == '-':
            return left_val - right_val
        elif node.op == '*':
            return left_val * right_val
        elif node.op == '/':
            if right_val == 0:
                raise InterpreterError("Division by zero")
            return left_val / right_val
        elif node.op == '**':
            return left_val ** right_val

    def interpret(self):
        """Interpret the full expression and return the result."""
        tree = self.parser.parse()
        if tree is None:
            return 0
        return self.visit(tree)


# --- Error Classes ---
class LexerError(Exception):
    pass


class ParserError(Exception):
    pass


class InterpreterError(Exception):
    pass


# --- Main Evaluation Function ---
def evaluate_expression(text: str) -> str:
    """
    High-level function to take a raw string,
    run it through the full pipeline, and return a formatted result.
    """
    if not text:
        return ""

    try:
        lexer = Lexer(text)
        parser = Parser(lexer)
        interpreter = Interpreter(parser)
        result = interpreter.interpret()

        if isinstance(result, (int, float)):
            if result == int(result):
                return str(int(result))
            else:
                return f"{result:.10g}"
        return str(result)

    except (LexerError, ParserError) as e:
        print(f"Syntax Error: {e}")
        return f"Error: {e}"  # Return the full error message
    except (InterpreterError, ZeroDivisionError, ValueError) as e:
        print(f"Runtime Error: {e}")
        return f"Error: {e}"
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return f"Error: {e}"


# --- Main block for testing this file directly ---
if __name__ == "__main__":
    print("--- KaCalc Core Unit Tests ---")

    tests = {
        "5+3": "8",  # Test no spaces
        "5 + 3": "8",  # Test spaces
        "10 - 2 * 3": "4",
        "(10 - 2) * 3": "24",
        "5 + -3": "2",
        "sqrt(9)": "3",
        "2 * sqrt(16) + 1": "9",
        "2**3": "8",  # Test **
        "2 + 3**2": "11",
        "(2 + 3)**2": "25",
        "10 / 0": "Error: Division by zero",
        "sqrt(-4)": "Error: Domain error: sqrt of negative number",
        "5 + (": "Error: Invalid syntax. Expected NUMBER, got EOF"
    }

    for expr, expected in tests.items():
        result = evaluate_expression(expr)
        status = "✅" if result == expected else "❌"
        print(f"{status} Expr: '{expr}' -> Result: {result} (Expected: {expected})")

    # Interactive loop
    print("\nEnter expressions to test (or 'exit' to quit):")
    while True:
        try:
            text = input("KaCalc> ")
            if text.lower() == 'exit':
                break
            print(f"Result: {evaluate_expression(text)}")
        except EOFError:
            break

