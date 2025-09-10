from scriptum.lexer import Lexer, KEYWORDS, TokenType

def test_empty_input():
    code = ""
    lex = Lexer(code)
    tokens = lex.tokenize()
    assert tokens == []

def test_while():
    code = "while"
    lex = Lexer(code)
    token = lex.next_token()
    assert code == token.value
    assert TokenType.WHILE == token.type

def test_if():
    code = "if"
    lex = Lexer(code)
    token = lex.next_token()
    assert code == token.value
    assert TokenType.IF == token.type

def test_else():
    code = "else"
    lex = Lexer(code)
    token = lex.next_token()
    assert code == token.value
    assert TokenType.ELSE == token.type

def test_return():
    code = "return"
    lex = Lexer(code)
    token = lex.next_token()
    assert code == token.value
    assert TokenType.RETURN == token.type

def test_let():
    code = "let"
    lex = Lexer(code)
    token = lex.next_token()
    assert code == token.value
    assert TokenType.LET == token.type

def test_and_or():
    code = {
        "and": TokenType.AND,
        "or": TokenType.OR
    }
    for k, v in code.items():
        lex = Lexer(k)
        token = lex.next_token()
        assert token.value == k
        assert token.type == v

def test_true_false():
    code = {
        "true": TokenType.TRUE,
        "false": TokenType.FALSE
    }
    for k, v in code.items():
        lex = Lexer(k)
        token = lex.next_token()
        assert token.value == k
        assert token.type == v

def test_comment():
    code = "# This is a comment"
    lex = Lexer(code, ignore_comments=False)
    token = lex.next_token()
    assert code == token.value
    assert TokenType.COMMENT == token.type

def test_string():
    code = '"This is a string!"'
    lex = Lexer(code)
    token = lex.next_token()
    assert "This is a string!" == token.value
    assert TokenType.STRING == token.type

def test_identifier():
    code = "i_am_identifier"
    lex = Lexer(code)
    token = lex.next_token()
    assert code == token.value
    assert TokenType.IDENTIFIER == token.type

def test_dot():
    code = "."
    lex = Lexer(code)
    token = lex.next_token()
    assert code == token.value
    assert TokenType.DOT == token.type

def test_assign():
    code = "="
    lex = Lexer(code)
    token = lex.next_token()
    assert code == token.value
    assert TokenType.ASSIGN == token.type

def test_comparisons():
    code = {
        "==": TokenType.EQUAL,
        "<": TokenType.LT,
        "<=": TokenType.LT_EQ,
        ">": TokenType.GT,
        ">=": TokenType.GT_EQ,
        "!=": TokenType.NOT_EQ
    }
    for k, v in code.items():
        lex = Lexer(k)
        token = lex.next_token()
        assert token.value == k
        assert token.type == v

def test_comma():
    code = ","
    lex = Lexer(code)
    token = lex.next_token()
    assert code == token.value
    assert TokenType.COMMA == token.type

def test_colon():
    code = ":"
    lex = Lexer(code)
    token = lex.next_token()
    assert code == token.value
    assert TokenType.COLON == token.type

def test_number_int():
    codes = ["10", "-100"]
    for code in codes:
        lex = Lexer(code)
        token = lex.next_token()
        assert int(code) == token.value
        assert TokenType.INT == token.type

def test_number_float():
    codes = ["3.14159", "-0.12", ".0123", "-2.5"]
    for code in codes:
        lex = Lexer(code)
        token = lex.next_token()
        assert float(code) == token.value
        assert TokenType.FLOAT == token.type

def test_arithmetic():
    code = {
        "-": TokenType.MINUS,
        "+": TokenType.PLUS,
        "*": TokenType.STAR,
        "/": TokenType.SLASH
    }
    for k, v in code.items():
        lex = Lexer(k)
        token = lex.next_token()
        assert token.value == k
        assert token.type == v

def test_brackets():
    code = {
        "[": TokenType.LBRACK,
        "]": TokenType.RBRACK,
        "(": TokenType.LPAREN,
        ")": TokenType.RPAREN,
        "{": TokenType.LBRACE,
        "}": TokenType.RBRACE
    }
    for k, v in code.items():
        lex = Lexer(k)
        token = lex.next_token()
        assert token.value == k
        assert token.type == v

def test_keywords():
    for keyword, type in KEYWORDS.items():
        lex = Lexer(keyword)
        token = lex.next_token()
        assert keyword == token.value
        assert type == token.type

def test_expression():
    code = "1 + 2"
    lex = Lexer(code)
    tokens = lex.tokenize()
    assert len(tokens) == 3
    assert tokens[0].type == TokenType.INT
    assert tokens[0].value == 1
    assert tokens[1].type == TokenType.PLUS
    assert tokens[1].value == "+"
    assert tokens[2].type == TokenType.INT
    assert tokens[2].value == 2