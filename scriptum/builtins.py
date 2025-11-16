# type: ignore
from llvmlite import ir
from scriptum.ast import SymbolEntry

def declare_malloc(module, symbol_table):
    malloc_ty = ir.FunctionType(ir.PointerType(ir.IntType(8)), [ir.IntType(64)])
    malloc = ir.Function(module, malloc_ty, name="malloc")
    symbol_table["malloc"] = SymbolEntry(variable_addr=malloc, static_type=malloc_ty)

def declare_builtins(module, symbol_table):
    declare_malloc(module, symbol_table)
