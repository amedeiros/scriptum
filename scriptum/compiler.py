# type: ignore
import sys
import os
from llvmlite import binding, ir
from scriptum.lexer import Lexer
from scriptum.parser import Parser
from scriptum.ast import SymbolTable
from scriptum.semantic_analyzer import analyze
import scriptum.builtins as builtins

CODE = open("code.fun").read()

def repl():
    while True:
        code = input(">>> ")
        if code == "exit":
            break
        module = build_module(code)
        execute_module(module)

def build_module(code=CODE):
    lexer = Lexer(code)
    parser = Parser(lexer)
    ast = parser.parse()
    module = ir.Module(name="my_module")
    # Set the target triple to the host's triple
    module.triple = binding.get_default_triple()
    builder = ir.IRBuilder()
    symbol_table = SymbolTable()
    # Declare built-in functions
    builtins.declare_builtins(module, symbol_table)

    func_type = ir.FunctionType(ir.VoidType(), [])
    main_func = ir.Function(module, func_type, name="main")
    block = main_func.append_basic_block(name="entry")
    builder = ir.IRBuilder(block)
    for node in ast:
        node.codegen(builder, module, symbol_table)
    builder.ret_void()
    return module

if __name__ == "__main__":
    # Validate command line arguments
    if len(sys.argv) < 2:
        print("Usage: python -m scriptum.compiler <source_file>")
        sys.exit(1)

    # Read source file
    source_file = sys.argv[1]
    with open(source_file, "r") as f:
        code = f.read()

    # Build LLVM module
    module = build_module(code)

    # Write LLVM IR to file
    root_dir = "./bin/"
    root_file = source_file.rsplit(".", 1)[0]
    llvm_instructions = root_dir + root_file + ".ll"
    with open(llvm_instructions, "w") as f:
        f.write(str(module))
    print(f"LLVM IR written to {llvm_instructions}")

    # Write object file and executable
    obj_file = root_dir + root_file + ".o"
    executable_file = root_dir + root_file
    os.system(f"llc -filetype=obj {llvm_instructions} -o {obj_file}")
    print(f"Object file written to {obj_file}")
    os.system(f"clang {obj_file} -o {executable_file}")
    print(f"Executable written to {executable_file}")
