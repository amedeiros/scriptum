# type: ignore
from scriptum.lexer import Lexer, Token, TokenType
from scriptum.ast import *

class ParseError(Exception):
    pass

# Precedence
LOWEST    = 0
OR        = 1
AND       = 2
EQUALS    = 3
LT_GT     = 4
SUM       = 5
PRODUCT   = 6
PREFIX    = 7
CALL      = 8
SUBSCRIPT = 9
DOT       = 10

PRECEDENCES = {}
PRECEDENCES[TokenType.ASSIGN]   = EQUALS
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
PRECEDENCES[TokenType.LBRACK]   = SUBSCRIPT
PRECEDENCES[TokenType.DOT]      = DOT


class Parser:
    def __init__(self, lexer: Lexer):
        self.lexer = lexer
        self.current_token = lexer.next_token()
        self.peek_token = lexer.next_token()
        self.prefix_parse_funcs = {}
        self.infix_parse_funcs = {}
        self._load_prefix_parse_funcs()
        self._load_infix_parse_funcs()
        self.lambda_count = 0

    def _load_prefix_parse_funcs(self) -> None:
        self._register_prefix(TokenType.IDENTIFIER, self._parse_identifier)
        self._register_prefix(TokenType.INT, self._parse_int)
        self._register_prefix(TokenType.FLOAT, self._parse_float)
        self._register_prefix(TokenType.STRING, self._parse_string)
        self._register_prefix(TokenType.TRUE, self._parse_boolean)
        self._register_prefix(TokenType.FALSE, self._parse_boolean)
        self._register_prefix(TokenType.PLUS, self._parse_prefix_expression)
        self._register_prefix(TokenType.MINUS, self._parse_prefix_expression)
        self._register_prefix(TokenType.BANG, self._parse_prefix_expression)
        self._register_prefix(TokenType.IF, self._parse_if_expression)
        self._register_prefix(TokenType.WHILE, self._parse_while_expression)
        self._register_prefix(TokenType.LPAREN, self._parse_grouped_expression)
        self._register_prefix(TokenType.FUNCTION, self._parse_function_literal)
        self._register_prefix(TokenType.LBRACK, self._parse_array_literal)
        self._register_prefix(TokenType.IMPORT, self._parse_import_statement)
        self._register_prefix(TokenType.FROM, self._parse_from_statement)

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
        self._register_infix(TokenType.ASSIGN, self._parse_assign_expression)
        self._register_infix(TokenType.LBRACK, self._parse_subscript_expression)
        self._register_infix(TokenType.DOT, self._parse_infix_expression)

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

    def _parse_assign_expression(self, left: ASTNode) -> AssignNode:
        assign = AssignNode(self.current_token)
        assign.add_child(left)
        self._consume(TokenType.ASSIGN)
        assign.add_child(self._parse_expression(LOWEST))
        return assign

    def _parse_subscript_expression(self, base: ASTNode) -> SubscriptNode:
        # The current token is LBRACK
        subscript = SubscriptNode(self.current_token)
        self._advance()  # consume '['
        index_expr = self._parse_expression(LOWEST)
        subscript.add_child(base)      # base, e.g., arr
        subscript.add_child(index_expr) # index, e.g., 0
        self._consume(TokenType.RBRACK)
        return subscript

    def _parse_infix_expression(self, left: ASTNode) -> BinaryOpNode:
        # Array replication syntax
        if self.current_token.type == TokenType.STAR and left.token.type == TokenType.LBRACK:
            expression = ArrayReplicationNode(left.token)
        elif self.current_token.type == TokenType.DOT:
            expression = DotNode(self.current_token)
        else:
            expression = BinaryOpNode(self.current_token)

        expression.add_child(left)
        self._advance()
        expression.add_child(self._parse_expression(LOWEST))
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

    def _parse_while_expression(self) -> WhileNode:
        expression = WhileNode(self.current_token)
        self._consume(TokenType.WHILE)
        self._consume(TokenType.LPAREN)
        # Condition
        expression.add_child(self._parse_expression(LOWEST))
        self._consume(TokenType.RPAREN)
        # Consequence
        expression.add_child(self._parse_block_statement())
        return expression
    
    def _parse_function_literal(self) -> FunctionNode:
        function = FunctionNode(self.current_token)
        self._consume(TokenType.FUNCTION)
        # Parse function parameters
        if self._consume(TokenType.LPAREN):
            function.children.append(self._parse_function_params())
        
        # Parse return type defaults to void
        if self._check(TokenType.COLON):
            self._consume(TokenType.COLON)
            function.static_return_type = self._parse_static_type()

        # Parse function body
        function.children.append(self._parse_block_statement())
        return function
    
    def _parse_function_params(self) -> list:
        identifiers = []
        default_arg_found = False
        if self._check(TokenType.RPAREN):
            self._advance()
            return identifiers
        while not self._check(TokenType.RPAREN) and not self._is_eof():
            # Parse the argument identifier
            arg_ident = self._parse_argument_identifier()
            if not arg_ident:
                self._error(self.current_token, "expected function argument identifier")
            # Add the identifier to the list of parameters
            identifiers.append(arg_ident)
            # Parse default value if any
            if self._check(TokenType.ASSIGN):
                default_arg_found = True
                self._consume(TokenType.ASSIGN)
                # Parse default value expression
                default_value_expr = self._parse_expression(LOWEST)
                arg_ident.default_value = default_value_expr
            elif default_arg_found:
                self._error(self.current_token, "non-default argument follows default argument")
            # Parse comma if more parameters
            if not self._check(TokenType.RPAREN):
                self._consume(TokenType.COMMA)
        self._consume(TokenType.RPAREN)
        return identifiers

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
        # Parse let statement
        let = LetNode(self.current_token)
        self._consume(TokenType.LET)
        # Parse identifier
        let.children.append(self._parse_identifier())
        # Parse the expression assigned to the identifier
        self._consume(TokenType.ASSIGN)
        let.children.append(self._parse_expression(LOWEST))
        # Check for function definition and assign the identifier name to the function name
        if isinstance(let.children[len(let.children)-1], FunctionNode):
            let.children[len(let.children)-1].name = let.children[0].token.value

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
    
    def _parse_argument_identifier(self) -> ArgumentIdentifierNode:
        ident = self.current_token
        if self._match(TokenType.IDENTIFIER):
            # Parse static type
            self._consume(TokenType.COLON)
            static_type = self._parse_static_type()
            arg_node = ArgumentIdentifierNode(ident, static_type)
            # Parse callable argument and return types
            if static_type == TokenType.TYPE_CALLABLE or static_type == TokenType.TYPE_ARRAY:
                if self._check(TokenType.LBRACK):
                    self._consume(TokenType.LBRACK)
                    callable_arg_types = []
                    while not self._check(TokenType.RBRACK) and not self._is_eof():
                        callable_arg_types.append(self._parse_static_type())
                        if not self._check(TokenType.RBRACK):
                            self._consume(TokenType.COMMA)
                    self._consume(TokenType.RBRACK)
                    arg_node.callable_arg_types = callable_arg_types
                # Parse return type for callable
                if self._check(TokenType.COLON):
                    self._consume(TokenType.COLON)
                    arg_node.callable_return_type = self._parse_static_type()

            return arg_node
        return None


    def _parse_array_literal(self) -> ArrayLiteralNode:
        array = ArrayLiteralNode(self.current_token)
        self._consume(TokenType.LBRACK)
        while not self._check(TokenType.RBRACK) and not self._is_eof():
            array.add_child(self._parse_expression(LOWEST))
            if not self._check(TokenType.RBRACK):
                self._consume(TokenType.COMMA)
        self._consume(TokenType.RBRACK)
        # Infer static type if possible
        if len(array.children) > 0:
            if isinstance(array.children[0], ArrayLiteralNode):
                array.static_type = ir.PointerType(vector_struct_ty)
            elif not isinstance(array.children[0], IdentifierNode):
                array.static_type = array.children[0].gentype()

        return array

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
        # Compile time append function
        if function_identifier.token.value == "append":
            expression = AppendNode(function_identifier.token)
        elif function_identifier.token.value == "remove":
            expression = ArrayRemoveNode(function_identifier.token)
        elif function_identifier.token.value == "pop":
            expression = ArrayPopNode(function_identifier.token)
        elif function_identifier.token.value == "insert":
            expression = ArrayInsertNode(function_identifier.token)
        elif function_identifier.token.value == "index_of":
            expression = ArrayIndexOfNode(function_identifier.token)
        else:
            expression = FunctionCallNode(function_identifier.token)

        expression.children.extend(self._parse_call_arguments())
        return expression
    
    def _parse_call_arguments(self) -> list[ASTNode]:
        args = []
        if self._check(TokenType.LPAREN):
            self._consume(TokenType.LPAREN)
            while not self._check(TokenType.RPAREN) and not self._is_eof():
                argument = self._parse_expression(LOWEST)
                if argument.token.type == TokenType.FUNCTION:
                    argument.name = f"{self.lambda_count}_lambda"
                    self.lambda_count += 1

                args.append(argument)
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

    def _parse_from_statement(self) -> ASTNode:
        # Parse the 'from' keyword and module name
        from_token = self.current_token
        self._consume(TokenType.FROM)
        module_name_token = self.current_token
        self._consume(TokenType.IDENTIFIER)

        # Parse the import statement
        from_node = FromImportNode(from_token, module_name_token)
        from_node.children.append(self._parse_import_statement())
        
        return from_node
    
    def _parse_import_statement(self) -> ASTNode:
        import_node = ImportNode(self.current_token)
        self._consume(TokenType.IMPORT)
        module_name_token = self.current_token
        if not self._check(TokenType.STAR) and not self._check(TokenType.IDENTIFIER):
            self._error(self.current_token, f"expected module name or '*' found {self.current_token.value} instead")
        
        self._consume(self.current_token.type)  # consume IDENTIFIER or STAR

        alias_token = None
        if self._check(TokenType.AS):
            self._consume(TokenType.AS)
            alias_token = self.current_token
            self._consume(TokenType.IDENTIFIER)

        module_identifier = ModuleIdentifierNode(module_name_token, alias_token)
        import_node.add_child(module_identifier)
        
        while self._check(TokenType.COMMA):
            self._consume(TokenType.COMMA)
            module_name_token = self.current_token
            self._consume(TokenType.IDENTIFIER)

            alias_token = None
            if self._check(TokenType.AS):
                self._consume(TokenType.AS)
                alias_token = self.current_token
                self._consume(TokenType.IDENTIFIER)

            module_identifier = ModuleIdentifierNode(module_name_token, alias_token)
            import_node.add_child(module_identifier)

        return import_node
    
    def _parse_static_type(self) -> TokenType:
        if self._check(TokenType.TYPE_INT):
            self._advance()
            return TokenType.TYPE_INT
        if self._check(TokenType.TYPE_FLOAT):
            self._advance()
            return TokenType.TYPE_FLOAT
        if self._check(TokenType.TYPE_STRING):
            self._advance()
            return TokenType.TYPE_STRING
        if self._check(TokenType.TYPE_BOOL):
            self._advance()
            return TokenType.TYPE_BOOL
        if self._check(TokenType.TYPE_ARRAY):
            self._advance()
            return TokenType.TYPE_ARRAY
        if self._check(TokenType.TYPE_CALLABLE):
            self._advance()
            return TokenType.TYPE_CALLABLE

        self._error(self.current_token, f"expected type annotation (int, float, str) found {self.current_token.value} instead")

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
        print(f"{indent}{node.__class__.__name__}: {node.token.value} ")
        for child in node.children:
            if isinstance(child, list):
                print_ast(child, level + 1)
            else:
                print_ast([child], level + 1)

def __main__():
    code = """
    other_module.some_function(10, 20)

    # import x
    # import x, y
    # import x, y, z as w
    # from x import y
    # from x import y, z as w
    # from x import *
    """
    lexer = Lexer(code)
    parser = Parser(lexer)
    ast = parser.parse()
    print_ast(ast)

if __name__ == "__main__":
    __main__()