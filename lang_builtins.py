# type: ignore
from llvmlite import ir
from lang_ast import value_struct_ty, TYPE_INT, TYPE_FLOAT, TYPE_BOOL

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

def declare_unbox(module, symbol_table, builder):
    fn_name = "unbox_value"
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
