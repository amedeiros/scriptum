# type: ignore
from llvmlite import ir

NATIVE_FUNCS = {"printf", "puts", "strcat", "strcmp"}

# Begin built-in printing functions
def declare_printf(module, symbol_table):
    printf_ty = ir.FunctionType(ir.IntType(32), [ir.PointerType(ir.IntType(8))], var_arg=True)
    printf = ir.Function(module, printf_ty, name="printf")
    symbol_table["printf"] = printf

def declare_puts(module, symbol_table):
    puts_ty = ir.FunctionType(ir.IntType(32), [ir.PointerType(ir.IntType(8))], var_arg=True)
    puts = ir.Function(module, puts_ty, name="puts")
    symbol_table["puts"] = puts

def declare_strcat(module, symbol_table):
    strcat_ty = ir.FunctionType(ir.PointerType(ir.IntType(8)), [ir.PointerType(ir.IntType(8)), ir.PointerType(ir.IntType(8))])
    strcat = ir.Function(module, strcat_ty, name="strcat")
    symbol_table["strcat"] = strcat

def declare_strcmp(module, symbol_table):
    strcmp_ty = ir.FunctionType(ir.IntType(32), [ir.PointerType(ir.IntType(8)), ir.PointerType(ir.IntType(8))])
    strcmp = ir.Function(module, strcmp_ty, name="strcmp")
    symbol_table["strcmp"] = strcmp

def declare_builtins(module, symbol_table):
    declare_printf(module, symbol_table)
    declare_puts(module, symbol_table)
    declare_strcat(module, symbol_table)
    declare_strcmp(module, symbol_table)
