import enum

class TokenType(enum.Enum):
    EOF        = "EOF"
    COMMENT    = "COMMENT"
    IDENTIFIER = "IDENTIFIER"
    RETURN     = "RETURN"
    LET        = "LET"
    FOREIGN    = "FOREIGN"
    DOT        = "DOT"
    FUNCTION   = "FUNCTION"
    COLON      = "COLON"
    COMMA      = "COMMA"
    ASSIGN     = "ASSIGN"
    SEMICOLON  = "SEMICOLON"
    AMPERSAND  = "AMPERSAND"

    # Comparisons
    EQUAL  = "EQUAL"
    LT_EQ  = "LT_EQ"
    GT_EQ  = "GT_EQ"
    NOT_EQ = "NOT_EQ"
    BANG   = "BANG"
    LT     = "LT"
    GT     = "GT"

    # Logical
    AND    = "AND"
    OR     = "OR"
    IF     = "IF"
    ELSE   = "ELSE"
    WHILE  = "WHILE"

    # Arithmetic
    MODULO = "MODULO"
    MINUS  = "MINUS"
    PLUS   = "PLUS"
    STAR   = "STAR"
    SLASH  = "SLASH"

    # Brackets
    LBRACE = "LBRACE"
    RBRACE = "RBRACE"
    LBRACK = "LBRACK"
    RBRACK = "RBRACK"
    LPAREN = "LPAREN"
    RPAREN = "RPAREN"

    # Native Types
    STRING = "STRING"
    INT    = "INT"
    FLOAT  = "FLOAT"
    TRUE   = "TRUE"
    FALSE  = "FALSE"

    # Static Types
    TYPE_CALLABLE = "TYPE_CALLABLE"
    TYPE_STRING   = "TYPE_STRING"
    TYPE_ARRAY    = "TYPE_ARRAY"
    TYPE_FLOAT    = "TYPE_FLOAT"
    TYPE_INT      = "TYPE_INT"
    TYPE_BOOL     = "TYPE_BOOL"
    TYPE_CHAR     = "TYPE_CHAR"
    TYPE_VOID     = "TYPE_VOID"

    # Importing
    IMPORT = "IMPORT"
    FROM   = "FROM"
    AS     = "AS"

EOF      = "\0"
KEYWORDS = {
    "if":       TokenType.IF,
    "else":     TokenType.ELSE,
    "while":    TokenType.WHILE,
    "return":   TokenType.RETURN,
    "let":      TokenType.LET,
    "foreign":  TokenType.FOREIGN,
    "import":   TokenType.IMPORT,
    "from":     TokenType.FROM,
    "as":       TokenType.AS,
    "and":      TokenType.AND,
    "or":       TokenType.OR,
    "true":     TokenType.TRUE,
    "false":    TokenType.FALSE,
}


class Token:
    def __init__(self, type: TokenType, value: any, row: int, column: int, file_name: str = ""):
        self.type   = type
        self.value  = value
        self.row    = row
        self.column = column
        self.file_name = file_name

    def __repr__(self):
        return f"Token({self.type}, {self.value}, {self.row}, {self.column}, {self.file_name})"
    
    def line_number(self):
        return f"{self.file_name} {self.row}:{self.column}"


class LexerError(Exception):
    pass


class Lexer:
    def __init__(self, source_code, file_name: str = "", ignore_comments: bool = True):
        self.source_code     = source_code
        self.ignore_comments = ignore_comments
        self.source_len      = len(source_code)
        self.file_name       = file_name
        self.column          = 0
        self.row             = 0
        self.ip              = 0

    # Begin Public API

    def tokenize(self):
        tokens = []
        while self._inbounds() and (cur := self.next_token()) and cur.value != EOF:
            tokens.append(cur)
        return tokens

    def next_token(self) -> Token:
        self._consume_ws()
        if not self._inbounds():
            return Token(TokenType.EOF, EOF, self.row, self.column, self.file_name)

        current = self._current_char()
        peek = self._peek()
        if current == "#":
            comment = self._consume_comment()
            if self.ignore_comments:
                return self.next_token()
            return comment
        if current == '"':
            return self._consume_string()
        if current.isalpha():
            return self._consume_identifier()
        if current.isnumeric():
            return self._consume_number()
        if current == "&":
            return Token(TokenType.AMPERSAND, *self._consume(), self.file_name)
        if current == ";":
            return Token(TokenType.SEMICOLON, *self._consume(), self.file_name)
        if current == "%":
            return Token(TokenType.MODULO, *self._consume(), self.file_name)
        if current == ",":
            return Token(TokenType.COMMA, *self._consume(), self.file_name)
        if current == ":":
            return Token(TokenType.COLON, *self._consume(), self.file_name)
        if current == "[":
            return Token(TokenType.LBRACK, *self._consume(), self.file_name)
        if current == "]":
            return Token(TokenType.RBRACK, *self._consume(), self.file_name)
        if current == "(":
            return Token(TokenType.LPAREN, *self._consume(), self.file_name)
        if current == ")":
            return Token(TokenType.RPAREN, *self._consume(), self.file_name)
        if current == "{":
            return Token(TokenType.LBRACE, *self._consume(), self.file_name)
        if current == "}":
            return Token(TokenType.RBRACE, *self._consume(), self.file_name)
        if current == "+":
            return Token(TokenType.PLUS, *self._consume(), self.file_name)
        if current == "*":
            return Token(TokenType.STAR, *self._consume(), self.file_name)
        if current == "/":
            return Token(TokenType.SLASH, *self._consume(), self.file_name)
        if current == "=":
            if peek and peek == "=":
                _, row, column = self._consume() # consume =
                self._consume() # consume =
                return Token(TokenType.EQUAL, "==", row, column, self.file_name)
            return Token(TokenType.ASSIGN, *self._consume(), self.file_name)
        if current == "!":
            if peek and peek == "=":
                _, row, column = self._consume() # consume !
                self._consume() # consume =
                return Token(TokenType.NOT_EQ, "!=", row, column, self.file_name)
            return Token(TokenType.BANG, *self._consume(), self.file_name)
        if current == "<":
            if peek and peek == "=":
                _, row, column = self._consume() # consume <
                self._consume() # consume =
                return Token(TokenType.LT_EQ, "<=", row, column, self.file_name)
            return Token(TokenType.LT, *self._consume(), self.file_name)
        if current == ">":
            if peek and peek == "=":
                _, row, column = self._consume() # consume >
                self._consume() # consume =
                return Token(TokenType.GT_EQ, ">=", row, column, self.file_name)
            return Token(TokenType.GT, *self._consume(), self.file_name)
        if current == ".":
            if peek and peek.isnumeric():
                return self._consume_number()
            return Token(TokenType.DOT, *self._consume(), self.file_name)
        if current == "-":
            # Number
            if peek and peek.isnumeric():
                return self._consume_number()
            # Function
            if peek and peek == ">":
                _, row, column = self._consume() # consume -
                self._consume() # consume >
                return Token(TokenType.FUNCTION, "->", row, column, self.file_name)
            # Minus
            return Token(TokenType.MINUS, *self._consume())
        return Token(TokenType.EOF, EOF, self.row, self.column, self.file_name)

    # Begin Private API

    def _inbounds(self) -> bool:
        return self.ip < self.source_len

    def _current_char(self) -> str:
        return self.source_code[self.ip]
    
    def _peek(self) -> str:
        if self.ip + 1 < self.source_len:
            return self.source_code[self.ip + 1]
        return None
    
    def _consume(self) -> str:
        char = self._current_char()
        column = self.column
        row = self.row
        self.ip += 1
        self.column += 1
        if char == "\n" or char == "\r": 
            self.row += 1
            self.column = 0

        return char, row, column

    def _consume_ws(self):
        while self._inbounds() and self._current_char().isspace():
            self._consume()

    def _consume_comment(self):
        start = self.ip
        char, row, column = self._consume()
        while self._inbounds() and char != "\n" and char != "\n":
            char, _, _ = self._consume()

        comment = self.source_code[start:self.ip]
        return Token(TokenType.COMMENT, comment, row, column, self.file_name)

    def _consume_identifier(self):
        start = self.ip
        _, row, column = self._consume()
        while self._inbounds() and \
            (self._current_char().isalpha() or self._current_char() == "_"):
            self._consume()

        identifier = self.source_code[start:self.ip]
        if identifier in KEYWORDS:
            return Token(KEYWORDS[identifier], identifier, row, column, self.file_name)
        return Token(TokenType.IDENTIFIER, identifier, row, column, self.file_name)

    def _consume_number(self) -> Token:
        start = self.ip
        _, row, column = self._consume()
        while self._inbounds() and \
            (self._current_char().isnumeric() or
             self._current_char() == "." or
             self._current_char() == "-"):
            self._consume()
        number = self.source_code[start:self.ip]
        try:
            number = int(number)
            return Token(TokenType.INT, number, row, column, self.file_name)
        except ValueError:
            try:
                number = float(number)
                return Token(TokenType.FLOAT, number, row, column, self.file_name)
            except ValueError:
                raise LexerError(f"Unknown expected a number found {number} instead at {row}:{column}")

    def _consume_string(self) -> Token:
        start = self.ip
        # Consume the "
        _, row, column = self._consume()
        char, _, _ = self._consume()
        while self._inbounds() and char != '"':
            char, _, _ = self._consume()

        if char != '"':
            raise LexerError(f"Expected '\"' found {self._current_char()} instead")
        
        string = self.source_code[start+1:self.ip-1] # skip over "
        string = bytes(string, "utf-8").decode("unicode_escape")
        return Token(TokenType.STRING, string, row, column, self.file_name)
