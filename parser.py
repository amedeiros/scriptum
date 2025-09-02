# type: ignore
from lexer import Lexer, Token, TokenType
from lang_ast import *

class ParseError(Exception):
    pass

# Precedence
LOWEST  = 0
OR      = 1
AND     = 2
EQUALS  = 3
LT_GT   = 4
SUM     = 5
PRODUCT = 6
PREFIX  = 7
CALL    = 8

PRECEDENCES = {}
PRECEDENCES[TokenType.EQUAL]    = EQUALS
PRECEDENCES[TokenType.NOT_EQ]   = EQUALS
PRECEDENCES[TokenType.AND]      = AND
PRECEDENCES[TokenType.OR]       = OR
PRECEDENCES[TokenType.LT]       = LT_GT
PRECEDENCES[TokenType.LT_EQ]    = LT_GT
PRECEDENCES[TokenType.GT]       = LT_GT
PRECEDENCES[TokenType.GT_EQ]    = LT_GT
PRECEDENCES[TokenType.PLUS]     = SUM
PRECEDENCES[TokenType.MINUS]    = SUM
PRECEDENCES[TokenType.SLASH]    = PRODUCT
PRECEDENCES[TokenType.STAR]     = PRODUCT
PRECEDENCES[TokenType.LPAREN]   = CALL


class Parser:
    def __init__(self, lexer: Lexer):
        self.lexer = lexer
        self.current_token = lexer.next_token()
        self.peek_token = lexer.next_token()
        self.prefix_parse_funcs = {}
        self.infix_parse_funcs = {}
        self._load_prefix_parse_funcs()
        self._load_infix_parse_funcs()

    def _load_prefix_parse_funcs(self) -> None:
        self._register_prefix(TokenType.IDENTIFIER, self._parse_identifier)
        self._register_prefix(TokenType.INT, self._parse_int)
        self._register_prefix(TokenType.FLOAT, self._parse_float)
        self._register_prefix(TokenType.STRING, self._parse_string)
        self._register_prefix(TokenType.TRUE, self._parse_boolean)
        self._register_prefix(TokenType.FALSE, self._parse_boolean)
        self._register_prefix(TokenType.MINUS, self._parse_prefix_expression)
        self._register_prefix(TokenType.BANG, self._parse_prefix_expression)
        self._register_prefix(TokenType.IF, self._parse_if_expression)
        self._register_prefix(TokenType.LPAREN, self._parse_grouped_expression)
        # self._register_prefix(TokenType.FUNCTION, self._parse_function_expression)

    def _load_infix_parse_funcs(self) -> None:
        self._register_infix(TokenType.AND, self._parse_infix_expression)
        self._register_infix(TokenType.OR, self._parse_infix_expression)
        self._register_infix(TokenType.PLUS, self._parse_infix_expression)
        self._register_infix(TokenType.MINUS, self._parse_infix_expression)
        self._register_infix(TokenType.SLASH, self._parse_infix_expression)
        self._register_infix(TokenType.STAR, self._parse_infix_expression)
        self._register_infix(TokenType.EQUAL, self._parse_infix_expression)
        self._register_infix(TokenType.NOT_EQ, self._parse_infix_expression)
        self._register_infix(TokenType.LT, self._parse_infix_expression)
        self._register_infix(TokenType.GT, self._parse_infix_expression)
        self._register_infix(TokenType.GT_EQ, self._parse_infix_expression)
        self._register_infix(TokenType.LT_EQ, self._parse_infix_expression)
        self._register_infix(TokenType.LPAREN, self._parse_call_expression)

    def _register_prefix(self, token_type: TokenType, parse_func) -> None:
        self.prefix_parse_funcs[token_type] = parse_func
    
    def _register_infix(self, token_type: TokenType, parse_func) -> None:
        self.infix_parse_funcs[token_type] = parse_func
    
    def parse(self) -> list[ASTNode]:
        statements = []
        while not self._is_eof():
            if self._check(TokenType.COMMENT):
                self._advance()
                continue
            statements.append(self._parse_statement())
        return statements

    def _parse_prefix_expression(self) -> PrefixNode:
        expression = PrefixNode(self.current_token)
        self._advance()
        expression.add_child(self._parse_expression(PREFIX))
        return expression
    
    def _parse_grouped_expression(self) -> ASTNode:
        self._consume(TokenType.LPAREN)
        expr = self._parse_expression(LOWEST)
        self._consume(TokenType.RPAREN)
        return expr

    def _parse_infix_expression(self, left: ASTNode) -> BinaryOpNode:
        expression = BinaryOpNode(self.current_token)
        expression.add_child(left)
        precedence = self._cur_precedence()
        self._advance()
        expression.add_child(self._parse_expression(precedence))
        return expression

    def _parse_if_expression(self) -> IfNode:
        expression = IfNode(self.current_token)
        self._consume(TokenType.IF)
        self._consume(TokenType.LPAREN)
        # Condition
        expression.add_child(self._parse_expression(LOWEST))
        self._consume(TokenType.RPAREN)
        # Consequence
        expression.add_child(self._parse_block_statement())
        # Alternative
        if self._check(TokenType.ELSE):
            self._consume(TokenType.ELSE)
            expression.add_child(self._parse_block_statement())
        return expression

    def _parse_block_statement(self) -> BlockNode:
        block = BlockNode(self.current_token)
        self._consume(TokenType.LBRACE)
        while not self._check(TokenType.RBRACE) and not self._is_eof():
            block.add_child(self._parse_statement())
        self._consume(TokenType.RBRACE)
        return block

    def _parse_statement(self):
        if self._check(TokenType.LET):
            return self._parse_let_statement()
        elif self._check(TokenType.RETURN):
            return self._parse_return_statement()
        else:
            return self._parse_expression(LOWEST)
        
    def _parse_let_statement(self) -> LetNode:
        let = LetNode(self.current_token)
        self._consume(TokenType.LET)
        let.children.append(self._parse_identifier())
        self._consume(TokenType.ASSIGN)
        let.children.append(self._parse_expression(LOWEST))

        return let
    
    def _parse_return_statement(self) -> ReturnNode:
        return_stmt = ReturnNode(self.current_token)
        self._consume(TokenType.RETURN)
        if self.current_token.type in (
            TokenType.IDENTIFIER, TokenType.INT, TokenType.FLOAT, TokenType.STRING, TokenType.LPAREN
        ):
            return_stmt.children.append(self._parse_expression(LOWEST))

        return return_stmt

    def _parse_identifier(self) -> IdentifierNode:
        ident = self.current_token
        if self._match(TokenType.IDENTIFIER):
            return IdentifierNode(ident)

    def _parse_int(self) -> NumberNode:
        int_token = self.current_token
        if self._match(TokenType.INT):
            return NumberNode(int_token)
    
    def _parse_float(self) -> NumberNode:
        float_token = self.current_token
        if self._match(TokenType.FLOAT):
            return NumberNode(float_token)
    
    def _parse_string(self) -> ASTNode:
        string_token = self.current_token
        if self._match(TokenType.STRING):
            return StringNode(string_token)
    
    def _parse_boolean(self) -> BooleanNode:
        boolean_token = self.current_token
        if self._match(TokenType.TRUE):
            return BooleanNode(boolean_token, True)
        if self._match(TokenType.FALSE):
            return BooleanNode(boolean_token, False)
        
        self._error(boolean_token, "expected TRUE or FALSE")
    
    def _parse_call_expression(self, function_identifier):
        # In this case the current token is ( instead function_identifier is the what we want.
        expression = FunctionCallNode(function_identifier.token)
        expression.children = self._parse_call_arguments()
        return expression
    
    def _parse_call_arguments(self) -> list[ASTNode]:
        args = []
        if self._check(TokenType.LPAREN):
            self._consume(TokenType.LPAREN)
            while not self._check(TokenType.RPAREN) and not self._is_eof():
                args.append(self._parse_expression(LOWEST))
                if not self._check(TokenType.RPAREN):
                    self._consume(TokenType.COMMA)
            self._consume(TokenType.RPAREN)
        return args

    def _parse_expression(self, precedence: int) -> ASTNode:
        prefix_func = self.prefix_parse_funcs.get(self.current_token.type)
        if not prefix_func:
            self._error(self.current_token, f"no prefix parse function registered for {self.current_token.type}")
        left_expr = prefix_func()
        while not self._is_eof() and precedence < self._cur_precedence():
            infix = self.infix_parse_funcs.get(self.current_token.type)
            if not infix:
                self._error(self.current_token, f"no infix parse function registered for {self.current_token.type}")
            left_expr = infix(left_expr)

        return left_expr

    def _match(self, types) -> bool:
        if not isinstance(types, list):
            types = [types]
        for type in types:
            if self._check(type):
                self._advance()
                return True
        return False
    
    def _consume(self, expected: TokenType) -> Token:
        if self._check(expected):
            return self._advance()
        self._error(self.current_token, f"expected {expected} found {self.current_token.type} instead")

    def _check_peek(self, type: TokenType) -> bool:
        if self._is_eof():
            return False
        return self.peek_token.type == type

    def _check(self, type: TokenType) -> bool:
        if self._is_eof():
            return False
        return self.current_token.type == type
    
    def _peek_precedence(self):
        p = PRECEDENCES.get(self.peek_token.type)
        return p if p else LOWEST

    def _cur_precedence(self):
        p = PRECEDENCES.get(self.current_token.type)
        return p if p else LOWEST

    def _is_eof(self) -> bool:
        return self.current_token.type == TokenType.EOF
    
    def _advance(self) -> Token:
        if not self._is_eof():
            self.current_token = self.peek_token
            self.peek_token = self.lexer.next_token()
        return self.current_token

    def _error(self, token: Token, msg: str):
        raise ParseError(f"Parse error at {token.row}:{token.column}: {msg}")

def print_ast(ast: list[ASTNode], level=0):
    indent = "  " * level
    for node in ast:
        print(f"{indent}{node.__class__.__name__}: {node.token.value}")
        for child in node.children:
            print_ast([child], level + 1)

if __name__ == "__main__":
    code = '''
let total = 1 + 1
let x = "apples"
let one = 1
let floating = 10.019
let truth = true
let falsity = false
let apples = floating
# return apples
if (truth) {
  printf("TRUE!!!")
} else {
  printf("FALSE!!!")
}
'''
    lexer = Lexer(code)
    parser = Parser(lexer)
    ast = parser.parse()
    print_ast(ast)
    from llvmlite import ir
    module = ir.Module(name="my_module")
    builder = ir.IRBuilder()
    symbol_table = {}
    # Declare built-in functions
    import lang_builtins as builtins
    builtins.declare_printf(module, symbol_table)

    func_type = ir.FunctionType(ir.VoidType(), [])
    main_func = ir.Function(module, func_type, name="main")
    block = main_func.append_basic_block(name="entry")
    builder = ir.IRBuilder(block)
    for node in ast:
        node.codegen(builder, module, symbol_table)
    print(module)