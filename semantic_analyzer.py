# type: ignore
from llvmlite import ir
from parser import Parser, print_ast
from lexer import Lexer
from lang_ast import *

TOKEN_TO_TYPE = {
    TokenType.INT: ir.IntType(32),
    TokenType.FLOAT: ir.FloatType(),
    TokenType.TRUE: ir.IntType(1),
    TokenType.FALSE: ir.IntType(1),
    TokenType.STRING: ir.ArrayType(ir.IntType(8), 8)
}

def analyze_function(ast, symbol_table):
    args = ast.children[0]
    if len(args) == 0:
        return # no arguments to process
    body = ast.children[1]
    if not isinstance(body, BlockNode):
        raise Exception(f"Expected block, got {body.token.type} at line {body.token.line_number}")

    # Process the body to determine argument types
    for arg in args:
        if not isinstance(arg, IdentifierNode):
            raise Exception(f"Expected identifier, got {arg.token.type} at line {arg.token.line_number}")
        for node in body.children:
            if isinstance(node, ReturnNode):
                for ret_child in node.children:
                    if isinstance(ret_child, FunctionCallNode):
                        if ret_child.token.type != TokenType.IDENTIFIER:
                            raise Exception(f"Expected identifier, got {ret_child.token.type} at line {ret_child.token.line_number}")
                        # Now try and check if the func is an argument
                        if arg.token.value == ret_child.token.value:
                            arg.type = ir.PointerType(ir.FunctionType(ir.PointerType(value_struct_ty), [child.type for child in ret_child.children]))
            elif isinstance(node, FunctionCallNode):
                if node.token.type != TokenType.IDENTIFIER:
                    raise Exception(f"Expected identifier, got {node.token.type} at line {node.token.line_number}")
                # Now try and check if the func is an argument
                if arg.token.value == node.token.value:
                    arg.type = ir.PointerType(ir.FunctionType(ir.PointerType(value_struct_ty), [child.type for child in node.children]))
            elif isinstance(node, LetNode):
                analyze_let(node, symbol_table, arg)

def analyze_let(node, symbol_table, func_arg = None):
    if len(node.children) != 2:
        raise Exception(f"Let node must have exactly 2 children, got {len(node.children)} at line {node.token.line_number}")
    ident = node.children[0]
    if not isinstance(ident, IdentifierNode):
        raise Exception(f"Expected identifier, got {ident.token.type} at line {ident.token.line_number}")
    
    rhs = node.children[1]
    if isinstance(rhs, FunctionNode):
        symbol_table[ident.token.value] = rhs
        analyze_function(rhs, symbol_table)
        ident.type = ir.PointerType(ir.FunctionType(ir.PointerType(value_struct_ty), [child.type for child in rhs.children[0]]))
    elif isinstance(rhs, FunctionCallNode):
        if func_arg and rhs.token.value == func_arg.token.value:
            func_arg.type = ir.PointerType(ir.FunctionType(ir.PointerType(value_struct_ty), [child.type for child in rhs.children]))
    elif isinstance(rhs, BinaryOpNode):
        for child in rhs.children:
            if isinstance(child, FunctionCallNode):
                if func_arg and child.token.value == func_arg.token.value:
                    func_arg.type = ir.PointerType(ir.FunctionType(ir.PointerType(value_struct_ty), [child.type for child in child.children]))
    else:
        type = TOKEN_TO_TYPE.get(rhs.token.type)
        if type:
            ident.type = type

def analyze(ast, symbol_table = SymbolTable()):
    for node in ast:
        if isinstance(node, LetNode):
            analyze_let(node, symbol_table)
        if isinstance(node, FunctionNode):
            raise Exception(f"Function should be defined with let at line {node.token.line_number}")

if __name__ == "__main__":
    code = '''
    let call = -> (func, x, y) {
        return func(x, y)
    }

    let add = -> (x, y) {
        return x + y
    }

    call(add, 2, 3)
    '''
    lexer = Lexer(code)
    parser = Parser(lexer)
    ast = parser.parse()
    analyze(ast)
    breakpoint()
    print_ast(ast)
