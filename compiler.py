# type: ignore
from llvmlite import binding, ir
from lexer import Lexer
from parser import Parser
from lang_ast import SymbolTable
import lang_builtins as builtins

CODE = open("code.fun").read()

# Initialize LLVM
binding.initialize()
binding.initialize_native_target()
binding.initialize_native_asmprinter()

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
    # print_ast(ast)
    module = ir.Module(name="my_module")
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
    # print(module)
    builder.ret_void()
    return module

if __name__ == "__main__":
    # Create an execution engine
    target = binding.Target.from_default_triple()
    target_machine = target.create_target_machine()
    backing_mod = binding.parse_assembly("")
    engine = binding.create_mcjit_compiler(backing_mod, target_machine)

    module = build_module()
    # Parse your IR
    llvm_ir = str(module)
    mod = binding.parse_assembly(llvm_ir)
    mod.verify()

    # Add the module and finalize
    engine.add_module(mod)
    engine.finalize_object()
    engine.run_static_constructors()

    # Get the address of the 'main' function and run it!
    main_ptr = engine.get_function_address("main")
    import ctypes
    main_func = ctypes.CFUNCTYPE(None)(main_ptr)
    main_func()
