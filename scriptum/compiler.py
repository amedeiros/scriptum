# type: ignore
import sys
import os
import glob
import pathlib
from llvmlite import binding, ir
from scriptum.lexer import Lexer, TokenType
from scriptum.parser import Parser
from scriptum.ast import SymbolTable
import scriptum.builtins as builtins


class Importer:
    def __init__(self, module_cache: dict):
        self.module_cache = module_cache
        self.search_paths = self._search_paths()

    def import_module(self, module_name: str, submodule_name: str = None):
        module_path, dir_found = self._resolve_module_path(module_name, submodule_name)
        found_name = pathlib.Path(module_path).stem # The module name might change if it's a submodule in a directory
        if module_path in self.module_cache:
            return self.module_cache[module_path]

        symbol_table = SymbolTable()
        imported_module = compile_file(module_path, self, symbol_table)
        write_file(imported_module, found_name, extension = ".ll", root_dir = "./bin/")
        self.module_cache[module_path] = (imported_module, symbol_table, found_name, dir_found)

        return self.module_cache[module_path]

    def _walk_paths(self, path):
        paths = set()
        for root, dirs, files in os.walk(path):
            full_dirs = [os.path.join(root, dir) for dir in dirs]
            paths.update(full_dirs)
            for full_dir in full_dirs:
                paths.update(self._walk_paths(full_dir))
        
        return paths

    def _search_paths(self):
        paths = []
        stdlib_path = os.path.join(os.getcwd(), "stdlib")
        if os.path.exists(stdlib_path):
            paths.append(stdlib_path)
            paths.extend(self._walk_paths(stdlib_path))
        else:
            paths.append("/usr/local/scriptum/stdlib")
        
        user_paths = os.environ.get("SCRIPTUMPATH", "").split(os.pathsep)
        paths.extend(user_paths)
        return paths

    def _resolve_module_path(self, module_name: str, submodule_name: str = None) -> (str, bool):
        for path in self.search_paths:
            potential_path = os.path.join(path, module_name + ".fun")
            if os.path.exists(potential_path):
                return potential_path, False
            if submodule_name is not None:
                potential_path = os.path.join(path, module_name, submodule_name + ".fun")
                if os.path.exists(potential_path):
                    return potential_path, True

        raise FileNotFoundError(f"Module {module_name} not found in search paths")

def write_file(data, filename, extension, root_dir = "./bin/") -> str:
    data_file = os.path.join(root_dir, pathlib.Path(filename).stem + extension)
    with open(data_file, "w") as f:
        f.write(str(data))
    
    return data_file

def compile_file(file_name, importer: Importer, symbol_table: SymbolTable, is_main: bool = False):
    # Read source code from file
    with open(file_name, "r") as f:
        code = f.read()

    # Lex and parse the source code
    lexer = Lexer(code)
    parser = Parser(lexer)
    ast = parser.parse()

    # Create LLVM module and symbol table
    module_name = pathlib.Path(file_name).stem
    module = ir.Module(name=module_name)
    module.triple = binding.get_default_triple()
    module_builder = ir.IRBuilder()

    # Add context to symbol table
    context = {
        "module_name": module_name,
        "is_main": is_main,
    }
    symbol_table["__context__"] = context

    # Compile the builtins to every module so they are available
    builtins.declare_builtins(module, symbol_table)

    # Define the wrapper function name for loose statements
    if is_main:
        wrap_block_name = "main"
    else:
        wrap_block_name = f"__init__{module_name}"

    # Create wrap function and entry block
    func_type = ir.FunctionType(ir.VoidType(), [])
    wrap_func = ir.Function(module, func_type, name=wrap_block_name)
    block = wrap_func.append_basic_block(name="entry")
    wrap_builder = ir.IRBuilder(block)
    for node in ast:
        # Handle imports module level
        if node.token.type == TokenType.IMPORT:
            for module_ident_node in node.children:
                if module_ident_node.token.type != TokenType.IDENTIFIER:
                    raise Exception("Invalid module name in import statement")
                module_name = module_ident_node.token.value
                imported_module, imported_symbols, module_name, dir_found = importer.import_module(module_name)

                # Alias namespace
                if module_ident_node.module_as_name:
                    alias = module_ident_node.module_as_name.value
                    symbol_table[alias] = imported_symbols

                # Functions should be "mangled" with module name prefix when not builtin or main
                for func in imported_module.functions:
                    if func.name not in module.globals and func.metadata.get("__init__") is None:
                        # Define a declaration for the imported function in the current module to later use with llvm linking resolver
                        symbol_table[func.name] = ir.Function(module, func.function_type, name=func.name)
        elif node.token.type == TokenType.FROM:
            import_node = node.children[0]
            root_module_name = node.module_name.value
            for module_ident_node in import_node.children:
                imported_module, imported_symbols, module_name, dir_found = importer.import_module(root_module_name, module_ident_node.token.value)
                if module_ident_node.token.type != TokenType.IDENTIFIER and module_ident_node.token.type != TokenType.STAR:
                    raise Exception("Invalid module name in from import statement")

                # We are importing all symbols
                if module_ident_node.token.type == TokenType.STAR:# or dir_found:
                    # Star import: import all symbols from the module
                    for func in imported_module.functions:
                        if func.name not in module.globals and "__init__" not in func.name:
                            # Define a declaration for the imported function in the current module to later use with llvm linking resolver
                            local_func_name = func.name.split(module_name + "_")[1]
                            symbol_table[local_func_name] = ir.Function(module, func.function_type, name=func.name)
                    continue

                # Namespace the imported module from the directory
                if dir_found:
                    # Is this an "as" alias?
                    if module_ident_node.module_as_name:
                        module_name = module_ident_node.module_as_name.value
                    symbol_table[module_name] = imported_symbols
                    for func in imported_module.functions:
                        if func.name not in module.globals and "__init__" not in func.name:
                            # Define a declaration for the imported function in the current module to later use with llvm linking resolver
                            symbol_table[func.name] = ir.Function(module, func.function_type, name=func.name)
                    continue

                # We are importing a specific function
                # Get local function name (with "as" alias if provided)
                local_func_name = module_ident_node.token.value
                if module_ident_node.module_as_name:
                    local_func_name = module_ident_node.module_as_name.value
                # Import function
                func_name = module_ident_node.mangled_name(imported_symbols)
                if func_name not in module.globals and func.metadata.get("__init__") is None:
                    # Define a declaration for the imported function in the current module to later use with llvm linking resolver
                    func = imported_symbols.get(func_name)
                    if not func:
                        raise Exception(f"Function {module_ident_node.token.value} not found in module {module_name}")
                    symbol_table[local_func_name] = ir.Function(module, func.function_type, name=func_name)
        elif node.token.type == TokenType.LET and node.children[0].token.type == TokenType.FUNCTION:
            # Function definition at module level
            node.codegen(module_builder, module, symbol_table)
        else: # Wrap loose statements in wrap_block_name function
            node.codegen(wrap_builder, module, symbol_table)
    
    wrap_builder.ret_void()
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
    module_cache = {}
    symbol_table = SymbolTable()
    importer = Importer(module_cache)
    optimized_module = compile_file(source_file, importer, symbol_table, is_main=True)

    # Write LLVM IR to file
    root_dir = os.path.abspath("./bin/")
    main_file = pathlib.Path(source_file).stem
    instructions_file = write_file(optimized_module, main_file, extension = ".ll", root_dir = root_dir)
    print(f"LLVM IR written to {instructions_file}")

    # Write object file and executable
    runtime_lib_path = "./ffi/lib"  # Path to the runtime library
    runtime_lib_name = "scriptum_runtime"  # Name of the runtime library (without the 'lib' prefix)

    # Collect all .ll files in the root directory
    ll_files = glob.glob(os.path.join(root_dir, "*.ll"))
    linked_ll_file = os.path.join(root_dir, "linked.ll")
    obj_file = os.path.join(root_dir, "linked.o")
    executable_file = os.path.join(root_dir, main_file)

    # Link all .ll files into one
    os.system(f"llvm-link {' '.join(ll_files)} -o {linked_ll_file}")
    print(f"Linked LLVM IR written to {linked_ll_file}")

    # Optimize the linked LLVM IR
    linked_opt_ll_file = os.path.join(root_dir, "linked_opt.ll")
    os.system(f"opt -O3 {linked_ll_file} -o {linked_opt_ll_file}")
    print(f"Optimized LLVM IR written to {linked_opt_ll_file}")

    # Compile linked .ll to object file
    os.system(f"llc -filetype=obj {linked_opt_ll_file} -o {obj_file}")
    print(f"Object file written to {obj_file}")

    # Link object file with the runtime library to create executable
    os.system(f"clang {obj_file} -L{runtime_lib_path} -l{runtime_lib_name} -o {executable_file}")
    print(f"Executable written to {executable_file}")
