# type: ignore
from llvmlite import ir
from lang_ast import value_struct_ty, vector_struct_ty, TYPE_INT, TYPE_FLOAT, TYPE_BOOL, TYPE_STRING, TYPE_ARRAY

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

def declare_strlen(module, symbol_table):
    strlen_ty = ir.FunctionType(ir.IntType(32), [ir.PointerType(ir.IntType(8))])
    strlen = ir.Function(module, strlen_ty, name="strlen")
    symbol_table["strlen"] = strlen

def declare_strcpy(module, symbol_table):
    strcpy_ty = ir.FunctionType(ir.IntType(32), [ir.PointerType(ir.IntType(8)), ir.PointerType(ir.IntType(8))])
    strcpy = ir.Function(module, strcpy_ty, name="strcpy")
    symbol_table["strcpy"] = strcpy

def declare_malloc(module, symbol_table):
    malloc_ty = ir.FunctionType(ir.PointerType(ir.IntType(8)), [ir.IntType(32)])
    malloc = ir.Function(module, malloc_ty, name="malloc")
    symbol_table["malloc"] = malloc

def declare_exit(module, symbol_table):
    exit_ty = ir.FunctionType(ir.VoidType(), [ir.IntType(32)])
    exit_fn = ir.Function(module, exit_ty, name="exit")
    symbol_table["exit"] = exit_fn

def declare_sizeof(module, symbol_table):
    sizeof_ty = ir.FunctionType(ir.IntType(32), [ir.IntType(32)])
    sizeof_fn = ir.Function(module, sizeof_ty, name="sizeof")
    symbol_table["sizeof"] = sizeof_fn

def declare_array_length(module, symbol_table):
    fn_ty = ir.FunctionType(ir.IntType(32), [ir.PointerType(vector_struct_ty)])
    fn = ir.Function(module, fn_ty, name="alen")
    block = fn.append_basic_block("entry")
    builder = ir.IRBuilder(block)
    arr_ptr = fn.args[0]
    length_ptr = builder.gep(arr_ptr, [ir.Constant(ir.IntType(32), 0), ir.Constant(ir.IntType(32), 2)])
    length = builder.load(length_ptr)
    builder.ret(length)
    symbol_table["alen"] = fn

def declare_array_get(module, symbol_table):
    fn_ty = ir.FunctionType(ir.PointerType(value_struct_ty), [ir.PointerType(vector_struct_ty), ir.IntType(32)])
    fn = ir.Function(module, fn_ty, name="aget")
    entry = fn.append_basic_block("entry")
    int_block = fn.append_basic_block("int")
    float_check_block = fn.append_basic_block("float_check")
    float_block = fn.append_basic_block("float")
    bool_check_block = fn.append_basic_block("bool_check")
    bool_block = fn.append_basic_block("bool")
    string_check_block = fn.append_basic_block("string_check")
    string_block = fn.append_basic_block("string")
    array_check_block = fn.append_basic_block("array_check")
    array_block = fn.append_basic_block("array")
    trap_block = fn.append_basic_block("trap")
    builder = ir.IRBuilder(entry)
    arr_ptr = fn.args[0]
    index = fn.args[1]

    # Get type tag and data pointer
    type_tag_ptr = builder.gep(arr_ptr, [ir.Constant(ir.IntType(32), 0), ir.Constant(ir.IntType(32), 0)])
    type_tag = builder.load(type_tag_ptr)
    data_ptr_ptr = builder.gep(arr_ptr, [ir.Constant(ir.IntType(32), 0), ir.Constant(ir.IntType(32), 1)])
    data_ptr = builder.load(data_ptr_ptr)

    # Branch chain
    is_int = builder.icmp_signed('==', type_tag, ir.Constant(ir.IntType(32), TYPE_INT))
    is_float = builder.icmp_signed('==', type_tag, ir.Constant(ir.IntType(32), TYPE_FLOAT))
    is_bool = builder.icmp_signed('==', type_tag, ir.Constant(ir.IntType(32), TYPE_BOOL))
    is_string = builder.icmp_signed('==', type_tag, ir.Constant(ir.IntType(32), TYPE_STRING))
    is_array = builder.icmp_signed('==', type_tag, ir.Constant(ir.IntType(32), TYPE_ARRAY))

    # Entry: check int, else float_check
    builder.cbranch(is_int, int_block, float_check_block)

    # INT block
    builder.position_at_start(int_block)
    elem_ptr = builder.gep(data_ptr, [index])
    elem = builder.load(elem_ptr)
    boxed = builder.alloca(value_struct_ty)
    type_ptr = builder.gep(boxed, [ir.Constant(ir.IntType(32), 0), ir.Constant(ir.IntType(32), 0)])
    builder.store(ir.Constant(ir.IntType(32), TYPE_INT), type_ptr)
    value_ptr = builder.gep(boxed, [ir.Constant(ir.IntType(32), 0), ir.Constant(ir.IntType(32), 1)])
    int_ptr = builder.bitcast(value_ptr, ir.PointerType(ir.IntType(32)))
    builder.store(elem, int_ptr)
    builder.ret(boxed)

    # FLOAT check block
    builder.position_at_start(float_check_block)
    builder.cbranch(is_float, float_block, bool_check_block)

    # FLOAT block
    builder.position_at_start(float_block)
    float_data_ptr = builder.bitcast(data_ptr, ir.PointerType(ir.FloatType()))
    elem_ptr = builder.gep(float_data_ptr, [index])
    elem = builder.load(elem_ptr)
    boxed = builder.alloca(value_struct_ty)
    type_ptr = builder.gep(boxed, [ir.Constant(ir.IntType(32), 0), ir.Constant(ir.IntType(32), 0)])
    builder.store(ir.Constant(ir.IntType(32), TYPE_FLOAT), type_ptr)
    value_ptr = builder.gep(boxed, [ir.Constant(ir.IntType(32), 0), ir.Constant(ir.IntType(32), 1)])
    float_ptr = builder.bitcast(value_ptr, ir.PointerType(ir.FloatType()))
    builder.store(elem, float_ptr)
    builder.ret(boxed)

    # BOOL check block
    builder.position_at_start(bool_check_block)
    builder.cbranch(is_bool, bool_block, string_check_block)

    # BOOL block
    builder.position_at_start(bool_block)
    bool_data_ptr = builder.bitcast(data_ptr, ir.PointerType(ir.IntType(1)))
    elem_ptr = builder.gep(bool_data_ptr, [index])
    elem = builder.load(elem_ptr)
    boxed = builder.alloca(value_struct_ty)
    type_ptr = builder.gep(boxed, [ir.Constant(ir.IntType(32), 0), ir.Constant(ir.IntType(32), 0)])
    builder.store(ir.Constant(ir.IntType(32), TYPE_BOOL), type_ptr)
    value_ptr = builder.gep(boxed, [ir.Constant(ir.IntType(32), 0), ir.Constant(ir.IntType(32), 1)])
    bool_ptr = builder.bitcast(value_ptr, ir.PointerType(ir.IntType(1)))
    builder.store(elem, bool_ptr)
    builder.ret(boxed)

    # STRING check block
    builder.position_at_start(string_check_block)
    builder.cbranch(is_string, string_block, array_check_block)

    # STRING block
    builder.position_at_start(string_block)
    elem_ptr = builder.gep(data_ptr, [index])
    elem = builder.load(elem_ptr)
    boxed = builder.alloca(value_struct_ty)
    type_ptr = builder.gep(boxed, [ir.Constant(ir.IntType(32), 0), ir.Constant(ir.IntType(32), 0)])
    builder.store(ir.Constant(ir.IntType(32), TYPE_STRING), type_ptr)
    value_ptr = builder.gep(boxed, [ir.Constant(ir.IntType(32), 0), ir.Constant(ir.IntType(32), 1)])
    str_ptr = builder.bitcast(value_ptr, ir.PointerType(elem.type))  # pointer to pointer type
    builder.store(elem, str_ptr)
    builder.ret(boxed)

    # ARRAY check block
    builder.position_at_start(array_check_block)
    builder.cbranch(is_array, array_block, trap_block)

    # ARRAY block
    builder.position_at_start(array_block)
    elem_ptr = builder.gep(data_ptr, [index])
    elem = builder.load(elem_ptr)
    boxed = builder.alloca(value_struct_ty)
    type_ptr = builder.gep(boxed, [ir.Constant(ir.IntType(32), 0), ir.Constant(ir.IntType(32), 0)])
    builder.store(ir.Constant(ir.IntType(32), TYPE_ARRAY), type_ptr)
    value_ptr = builder.gep(boxed, [ir.Constant(ir.IntType(32), 0), ir.Constant(ir.IntType(32), 1)])
    arr_ptr = builder.bitcast(value_ptr, ir.PointerType(elem.type))  # pointer to pointer type
    builder.store(elem, arr_ptr)
    builder.ret(boxed)

    # TRAP block
    builder.position_at_start(trap_block)
    trap_ty = ir.FunctionType(ir.VoidType(), [])
    trap_fn = module.declare_intrinsic('llvm.trap', (), trap_ty)
    builder.call(trap_fn, [])
    builder.ret(ir.Constant(ir.PointerType(value_struct_ty), None))

    symbol_table["aget"] = fn

def declare_unbox(module, symbol_table, builder):
    fn_name = "unbox"
    fn_ty = ir.FunctionType(ir.IntType(32), [ir.PointerType(value_struct_ty)])
    fn = ir.Function(module, fn_ty, name=fn_name)
    entry = fn.append_basic_block("entry")
    int_block = fn.append_basic_block("int")
    float_check_block = fn.append_basic_block("float_check")
    float_block = fn.append_basic_block("float")
    bool_check_block = fn.append_basic_block("bool_check")
    bool_block = fn.append_basic_block("bool")
    trap_block = fn.append_basic_block("trap")
    builder = ir.IRBuilder(entry)
    boxed = fn.args[0]
    type_tag_ptr = builder.gep(boxed, [ir.Constant(ir.IntType(32), 0), ir.Constant(ir.IntType(32), 0)])
    type_tag = builder.load(type_tag_ptr)
    is_int = builder.icmp_signed('==', type_tag, ir.Constant(ir.IntType(32), TYPE_INT))
    builder.cbranch(is_int, int_block, float_check_block)

    # int block
    builder.position_at_start(int_block)
    value_ptr = builder.gep(boxed, [ir.Constant(ir.IntType(32), 0), ir.Constant(ir.IntType(32), 1)])
    int_ptr = builder.bitcast(value_ptr, ir.PointerType(ir.IntType(32)))
    int_val = builder.load(int_ptr)
    builder.ret(int_val)

    # float_check block
    builder.position_at_start(float_check_block)
    is_float = builder.icmp_signed('==', type_tag, ir.Constant(ir.IntType(32), TYPE_FLOAT))
    builder.cbranch(is_float, float_block, bool_check_block)

    # float block
    builder.position_at_start(float_block)
    value_ptr = builder.gep(boxed, [ir.Constant(ir.IntType(32), 0), ir.Constant(ir.IntType(32), 1)])
    float_ptr = builder.bitcast(value_ptr, ir.PointerType(ir.FloatType()))
    float_val = builder.load(float_ptr)
    int_val = builder.fptosi(float_val, ir.IntType(32))
    builder.ret(int_val)

    # bool_check block
    builder.position_at_start(bool_check_block)
    is_bool = builder.icmp_signed('==', type_tag, ir.Constant(ir.IntType(32), TYPE_BOOL))
    builder.cbranch(is_bool, bool_block, trap_block)

    # bool block
    builder.position_at_start(bool_block)
    value_ptr = builder.gep(boxed, [ir.Constant(ir.IntType(32), 0), ir.Constant(ir.IntType(32), 1)])
    bool_ptr = builder.bitcast(value_ptr, ir.PointerType(ir.IntType(1)))
    bool_val = builder.load(bool_ptr)
    int_val = builder.zext(bool_val, ir.IntType(32))
    builder.ret(int_val)

    # trap block
    builder.position_at_start(trap_block)
    trap_ty = ir.FunctionType(ir.VoidType(), [])
    trap_fn = module.declare_intrinsic('llvm.trap', (), trap_ty)
    # Print a message
    msg_bytes = b"unbox: type mismatch %d\n\0"
    msg_type = ir.ArrayType(ir.IntType(8), len(msg_bytes))
    msg_global = ir.GlobalVariable(module, msg_type, name="unbox_type_mismatch_msg")
    msg_global.initializer = ir.Constant(msg_type, list(msg_bytes))
    msg_global.global_constant = True
    msg_ptr = builder.gep(msg_global, [ir.Constant(ir.IntType(32), 0), ir.Constant(ir.IntType(32), 0)])
    builder.call(symbol_table["printf"], [msg_ptr, type_tag])
    # Call their trap function
    builder.call(trap_fn, [])
    builder.ret(ir.Constant(ir.IntType(32), 0))
    symbol_table[fn_name] = fn

def declare_builtins(module, symbol_table, builder):
    declare_printf(module, symbol_table)
    declare_puts(module, symbol_table)
    declare_strcat(module, symbol_table)
    declare_strcmp(module, symbol_table)
    declare_strlen(module, symbol_table)
    declare_strcpy(module, symbol_table)
    declare_malloc(module, symbol_table)
    declare_unbox(module, symbol_table, builder)
    declare_exit(module, symbol_table)
    declare_sizeof(module, symbol_table)
    declare_array_length(module, symbol_table)
    declare_array_get(module, symbol_table)
