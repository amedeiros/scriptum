# type: ignore
from llvmlite import ir
from scriptum.ast import vector_struct_ty, SymbolEntry

# Begin built-in printing functions
def declare_printf(module, symbol_table):
    printf_ty = ir.FunctionType(ir.IntType(64), [ir.PointerType(ir.IntType(8))], var_arg=True)
    printf = ir.Function(module, printf_ty, name="printf")
    symbol_table["printf"] = SymbolEntry(variable_addr=printf, static_type=printf_ty)

def declare_puts(module, symbol_table):
    puts_ty = ir.FunctionType(ir.IntType(64), [ir.PointerType(ir.IntType(8))], var_arg=True)
    puts = ir.Function(module, puts_ty, name="puts")
    symbol_table["puts"] = SymbolEntry(variable_addr=puts, static_type=puts_ty)

def declare_strcat(module, symbol_table):
    strcat_ty = ir.FunctionType(ir.PointerType(ir.IntType(8)), [ir.PointerType(ir.IntType(8)), ir.PointerType(ir.IntType(8))])
    strcat = ir.Function(module, strcat_ty, name="strcat")
    symbol_table["strcat"] = SymbolEntry(variable_addr=strcat, static_type=strcat_ty)

def declare_strcmp(module, symbol_table):
    strcmp_ty = ir.FunctionType(ir.IntType(64), [ir.PointerType(ir.IntType(8)), ir.PointerType(ir.IntType(8))])
    strcmp = ir.Function(module, strcmp_ty, name="strcmp")
    symbol_table["strcmp"] = SymbolEntry(variable_addr=strcmp, static_type=strcmp_ty)

def declare_strlen(module, symbol_table):
    strlen_ty = ir.FunctionType(ir.IntType(64), [ir.PointerType(ir.IntType(8))])
    strlen = ir.Function(module, strlen_ty, name="strlen")
    symbol_table["strlen"] = SymbolEntry(variable_addr=strlen, static_type=strlen_ty)

def declare_strcpy(module, symbol_table):
    strcpy_ty = ir.FunctionType(ir.IntType(64), [ir.PointerType(ir.IntType(8)), ir.PointerType(ir.IntType(8))])
    strcpy = ir.Function(module, strcpy_ty, name="strcpy")
    symbol_table["strcpy"] = SymbolEntry(variable_addr=strcpy, static_type=strcpy_ty)

def declare_malloc(module, symbol_table):
    malloc_ty = ir.FunctionType(ir.PointerType(ir.IntType(8)), [ir.IntType(64)])
    malloc = ir.Function(module, malloc_ty, name="malloc")
    symbol_table["malloc"] = SymbolEntry(variable_addr=malloc, static_type=malloc_ty)

def declare_exit(module, symbol_table):
    exit_ty = ir.FunctionType(ir.VoidType(), [ir.IntType(64)])
    exit_fn = ir.Function(module, exit_ty, name="exit")
    symbol_table["exit"] = SymbolEntry(variable_addr=exit_fn, static_type=exit_ty)

def declare_sizeof(module, symbol_table):
    sizeof_ty = ir.FunctionType(ir.IntType(64), [ir.IntType(64)])
    sizeof_fn = ir.Function(module, sizeof_ty, name="sizeof")
    symbol_table["sizeof"] = SymbolEntry(variable_addr=sizeof_fn, static_type=sizeof_ty)

def declare_alen(module, symbol_table):
    alen_ty = ir.FunctionType(ir.IntType(64), [ir.PointerType(vector_struct_ty)])
    alen_fn = ir.Function(module, alen_ty, name="alen")
    symbol_table["alen"] = SymbolEntry(variable_addr=alen_fn, static_type=alen_ty)

def declare_pp_array(module, symbol_table):
    pp_array_ty = ir.FunctionType(ir.VoidType(), [ir.PointerType(vector_struct_ty)])
    pp_array_fn = ir.Function(module, pp_array_ty, name="pp_array")
    symbol_table["pp_array"] = SymbolEntry(variable_addr=pp_array_fn, static_type=pp_array_ty)

def declare_array_clear(module, symbol_table):
    array_clear_ty = ir.FunctionType(ir.VoidType(), [ir.PointerType(vector_struct_ty)])
    array_clear_fn = ir.Function(module, array_clear_ty, name="clear_array")
    symbol_table["clear"] = SymbolEntry(variable_addr=array_clear_fn, static_type=array_clear_ty)

def declare_array_reverse(module, symbol_table):
    array_reverse_ty = ir.FunctionType(ir.VoidType(), [ir.PointerType(vector_struct_ty)])
    array_reverse_fn = ir.Function(module, array_reverse_ty, name="reverse_array")
    symbol_table["reverse"] = SymbolEntry(variable_addr=array_reverse_fn, static_type=array_reverse_ty)

def declare_array_sort(module, symbol_table):
    array_sort_ty = ir.FunctionType(ir.VoidType(), [ir.PointerType(vector_struct_ty)])
    array_sort_fn = ir.Function(module, array_sort_ty, name="sort_array")
    symbol_table["sort"] = SymbolEntry(variable_addr=array_sort_fn, static_type=array_sort_ty)

def declare_array_functions(module, symbol_table):
    types = ["int", "float", "bool", "string", "array"]
    for data_type in types:
        # Declare create_<data_type>_array
        create_array_ty = ir.FunctionType(ir.PointerType(vector_struct_ty), [ir.IntType(64)])
        create_array = ir.Function(module, create_array_ty, name=f"create_{data_type}_array")
        symbol_table[f"create_{data_type}_array"] = SymbolEntry(variable_addr=create_array, static_type=create_array_ty)

        # Declare delete_<data_type>_array
        delete_array_ty = ir.FunctionType(ir.VoidType(), [ir.PointerType(vector_struct_ty)])
        delete_array = ir.Function(module, delete_array_ty, name=f"delete_{data_type}_array")
        symbol_table[f"delete_{data_type}_array"] = SymbolEntry(variable_addr=delete_array, static_type=delete_array_ty)

        # Declare <data_type>_array_get
        if data_type == "int":
            ret_type = ir.IntType(64)
        elif data_type == "float":
            ret_type = ir.FloatType()
        elif data_type == "bool":
            ret_type = ir.IntType(1)
        elif data_type == "string":
            ret_type = ir.PointerType(ir.IntType(8))
        elif data_type == "array":
            ret_type = ir.PointerType(vector_struct_ty)
        array_get_ty = ir.FunctionType(ret_type, [ir.PointerType(vector_struct_ty), ir.IntType(64)])
        array_get = ir.Function(module, array_get_ty, name=f"{data_type}_array_get")
        symbol_table[f"{data_type}_array_get"] = SymbolEntry(variable_addr=array_get, static_type=array_get_ty)

        # Declare <data_type>_array_set
        array_set_ty = ir.FunctionType(ir.VoidType(), [ir.PointerType(vector_struct_ty), ir.IntType(64), ret_type])
        array_set = ir.Function(module, array_set_ty, name=f"{data_type}_array_set")
        symbol_table[f"{data_type}_array_set"] = SymbolEntry(variable_addr=array_set, static_type=array_set_ty)

        # Declare <data_type>_array_push_back
        array_push_back_ty = ir.FunctionType(ir.VoidType(), [ir.PointerType(vector_struct_ty), ret_type])
        array_push_back = ir.Function(module, array_push_back_ty, name=f"{data_type}_array_push_back")
        symbol_table[f"{data_type}_array_push_back"] = SymbolEntry(variable_addr=array_push_back, static_type=array_push_back_ty)

        # Declare <data_type>_array_remove
        array_remove_ty = ir.FunctionType(ret_type, [ir.PointerType(vector_struct_ty), ir.IntType(64)])
        array_remove = ir.Function(module, array_remove_ty, name=f"{data_type}_array_remove")
        symbol_table[f"{data_type}_array_remove"] = SymbolEntry(variable_addr=array_remove, static_type=array_remove_ty)

        # Declare <data_type>_array_pop
        array_pop_ty = ir.FunctionType(ret_type, [ir.PointerType(vector_struct_ty)])
        array_pop = ir.Function(module, array_pop_ty, name=f"{data_type}_array_pop")
        symbol_table[f"{data_type}_array_pop"] = SymbolEntry(variable_addr=array_pop, static_type=array_pop_ty)

        # Declare <data_type>_array_insert
        array_insert_ty = ir.FunctionType(ir.VoidType(), [ir.PointerType(vector_struct_ty), ir.IntType(64), ret_type])
        array_insert = ir.Function(module, array_insert_ty, name=f"{data_type}_array_insert")
        symbol_table[f"{data_type}_array_insert"] = SymbolEntry(variable_addr=array_insert, static_type=array_insert_ty)

        # Declare <data_type>_array_index_of
        array_index_of_ty = ir.FunctionType(ir.IntType(64), [ir.PointerType(vector_struct_ty), ret_type])
        array_index_of = ir.Function(module, array_index_of_ty, name=f"{data_type}_array_index_of")
        symbol_table[f"{data_type}_array_index_of"] = SymbolEntry(variable_addr=array_index_of, static_type=array_index_of_ty)

        # Declare create_<data_type>_array_from_value
        create_array_from_value_ty = ir.FunctionType(ir.PointerType(vector_struct_ty), [ret_type, ir.IntType(64)])
        create_array_from_value = ir.Function(module, create_array_from_value_ty, name=f"create_{data_type}_array_from_value")
        symbol_table[f"create_{data_type}_array_from_value"] = SymbolEntry(variable_addr=create_array_from_value, static_type=create_array_from_value_ty)


def declare_builtins(module, symbol_table):
    declare_printf(module, symbol_table)
    declare_puts(module, symbol_table)
    declare_strcat(module, symbol_table)
    declare_strcmp(module, symbol_table)
    declare_strlen(module, symbol_table)
    declare_strcpy(module, symbol_table)
    declare_malloc(module, symbol_table)
    declare_exit(module, symbol_table)
    declare_sizeof(module, symbol_table)
    # Array functions
    declare_array_functions(module, symbol_table)
    declare_alen(module, symbol_table)
    declare_pp_array(module, symbol_table)
    declare_array_clear(module, symbol_table)
    declare_array_reverse(module, symbol_table)
    declare_array_sort(module, symbol_table)
