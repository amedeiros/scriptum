# type: ignore
from lexer import Token, TokenType
from abc import ABC, abstractmethod
from llvmlite import ir
from llvmlite.ir.builder import IRBuilder
from llvmlite.ir.module import Module
from lang_builtins import NATIVE_FUNCS

# Box type
value_struct_ty = ir.LiteralStructType([
    ir.IntType(32),
    ir.ArrayType(ir.IntType(8), 8),
])

# Type tags
TYPE_INT = 0
TYPE_FLOAT = 1
TYPE_BOOL = 2
TYPE_STRING = 3

class SymbolTable(dict[str, ir.Value]):
    def __init__(self, parent: "SymbolTable" = None):
        super().__init__()
        self.parent = parent

    def __setitem__(self, key: str, value: ir.Value):
        super().__setitem__(key, value)

    def __getitem__(self, key: str) -> ir.Value:
        try:
            return super().__getitem__(key)
        except KeyError:
            if self.parent:
                return self.parent[key]
            raise CodeGenError(f"Undefined variable: {key}")
    
    def get(self, key: str) -> ir.Value | None:
        v = super().get(key)
        if v is None and self.parent:
            return self.parent.get(key)
        return v

class CodeGenError(Exception):
    pass


class ASTNode(ABC):
    token: Token
    children: list["ASTNode"]

    def __init__(self, token: Token):
        self.token = token
        self.children = []

    def add_child(self, child: "ASTNode"):
        self.children.append(child)

    @abstractmethod
    def codegen(self, builder: IRBuilder, module: Module, symbol_table: dict[str, ir.Value]):
        pass

    @staticmethod
    def is_string_value(val):
        t = val.type
        return (
            isinstance(t, ir.PointerType) and
            isinstance(t.pointee, ir.ArrayType) and
            t.pointee.element == ir.IntType(8)
        )
    
    @staticmethod
    def is_boxed_value(val) -> bool:
        return isinstance(val.type, ir.types.PointerType) and val.type.pointee == value_struct_ty

    @staticmethod
    def box(val, builder):
        # Box based on value type
        if isinstance(val.type, ir.IntType) and val.type.width == 32:
            return ASTNode.box_int(builder, val)
        elif isinstance(val.type, ir.FloatType):
            return ASTNode.box_float(builder, val)
        elif isinstance(val.type, ir.IntType) and val.type.width == 1:
            return ASTNode.box_bool(builder, val)

        raise CodeGenError(f"Cannot box value {val}")
    
    @staticmethod
    def unbox(boxed, builder, module):
            # Use a builtin unbox function for all boxed values
            unbox_fn = ASTNode.get_or_create_unbox_function(module)
            return builder.call(unbox_fn, [boxed])

    @staticmethod
    def get_or_create_unbox_function(module):
        fn_name = "unbox_value"
        for fn in module.functions:
            if fn.name == fn_name:
                return fn
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
        return fn

    @staticmethod
    def box_int(builder, value):
        boxed = builder.alloca(value_struct_ty)
        # Store type tag
        type_ptr = builder.gep(boxed, [ir.Constant(ir.IntType(32), 0), ir.Constant(ir.IntType(32), 0)])
        builder.store(ir.Constant(ir.IntType(32), TYPE_INT), type_ptr)
        # Store value
        value_ptr = builder.gep(boxed, [ir.Constant(ir.IntType(32), 0), ir.Constant(ir.IntType(32), 1)])
        int_ptr = builder.bitcast(value_ptr, ir.PointerType(ir.IntType(32)))
        builder.store(value, int_ptr)
        return boxed

    @staticmethod
    def unbox_int(builder, boxed):
        # Get pointer to the value field
        value_ptr = builder.gep(boxed, [ir.Constant(ir.IntType(32), 0), ir.Constant(ir.IntType(32), 1)])
        # Bitcast to i32*
        int_ptr = builder.bitcast(value_ptr, ir.PointerType(ir.IntType(32)))
        return builder.load(int_ptr)
    
    @staticmethod
    def box_float(builder, value):
        boxed = builder.alloca(value_struct_ty)
        # Store type tag
        type_ptr = builder.gep(boxed, [ir.Constant(ir.IntType(32), 0), ir.Constant(ir.IntType(32), 0)])
        builder.store(ir.Constant(ir.IntType(32), TYPE_FLOAT), type_ptr)
        # Store value
        value_ptr = builder.gep(boxed, [ir.Constant(ir.IntType(32), 0), ir.Constant(ir.IntType(32), 1)])
        float_ptr = builder.bitcast(value_ptr, ir.PointerType(ir.FloatType()))
        builder.store(value, float_ptr)
        return boxed

    @staticmethod
    def unbox_float(builder, boxed):
        value_ptr = builder.gep(boxed, [ir.Constant(ir.IntType(32), 0), ir.Constant(ir.IntType(32), 1)])
        float_ptr = builder.bitcast(value_ptr, ir.PointerType(ir.FloatType()))
        return builder.load(float_ptr)
    
    @staticmethod
    def box_bool(builder, value):
        boxed = builder.alloca(value_struct_ty)
        # Store type tag
        type_ptr = builder.gep(boxed, [ir.Constant(ir.IntType(32), 0), ir.Constant(ir.IntType(32), 0)])
        builder.store(ir.Constant(ir.IntType(32), TYPE_BOOL), type_ptr)
        # Store value
        value_ptr = builder.gep(boxed, [ir.Constant(ir.IntType(32), 0), ir.Constant(ir.IntType(32), 1)])
        bool_ptr = builder.bitcast(value_ptr, ir.PointerType(ir.IntType(1)))
        builder.store(value, bool_ptr)
        return boxed

    @staticmethod
    def unbox_bool(builder, boxed):
        int_val = ASTNode.unbox_int(builder, boxed)
        if isinstance(int_val.type, ir.IntType) and int_val.type.width == 32:
            return builder.trunc(int_val, ir.IntType(1))
        # else:
        #     return int_val


class NumberNode(ASTNode):
    def __init__(self, token: Token):
        super().__init__(token)

    def codegen(self, builder, module, symbol_table):
        if self.token.type == TokenType.INT:
            return ir.Constant(ir.IntType(32), self.token.value)
        elif self.token.type == TokenType.FLOAT:
            return ir.Constant(ir.FloatType(), self.token.value)
        
        raise CodeGenError(f"Unknown number type {self.token.type}")

class StringNode(ASTNode):
    def __init__(self, token: Token):
        super().__init__(token)

    def codegen(self, builder, module, symbol_table):
        str_bytes = bytearray(self.token.value.encode("utf8")) + b"\00"  # null-terminated
        str_type = ir.ArrayType(ir.IntType(8), len(str_bytes))
        local_str = builder.alloca(str_type)
        # Store each byte (could use a loop or memcpy for efficiency)
        for i, b in enumerate(str_bytes):
            idx = ir.Constant(ir.IntType(32), i)
            ptr = builder.gep(local_str, [ir.Constant(ir.IntType(32), 0), idx])
            builder.store(ir.Constant(ir.IntType(8), b), ptr)
        return local_str

class BooleanNode(ASTNode):
    def __init__(self, token: Token, value: bool):
        super().__init__(token)
        self.value = value

    def codegen(self, builder, module, symbol_table):
        return ir.Constant(ir.IntType(1), 1 if self.value else 0)

class IdentifierNode(ASTNode):
    def __init__(self, token: Token):
        super().__init__(token)

    def codegen(self, builder, module, symbol_table):
        var_addr = symbol_table.get(self.token.value)
        if var_addr is None:
            raise CodeGenError(f"Undefined variable: {self.token.value}")
        
        # Handle unboxing types
        if self.is_boxed_value(var_addr):
            return self.unbox(var_addr, builder, module)

        # If the variable is a string return its pointer
        # TODO: Handle other data types requiring a pointer
        if isinstance(var_addr.type, ir.types.PointerType) and \
            isinstance(var_addr.type.pointee, ir.types.ArrayType) and \
                var_addr.type.pointee.element == ir.IntType(8):
            return var_addr
        # Otherwise return the loaded value
        return builder.load(var_addr)

class FunctionNode(ASTNode):
    def __init__(self, token: Token, name=None):
        super().__init__(token)
        self.name = name

    def codegen(self, builder, module, symbol_table):
        scoped_table = SymbolTable(parent=symbol_table)
        args = self.children[0]
        arg_count = len(args)
        arg_names = [arg.token.value for arg in args]
        arg_types = [ir.PointerType(value_struct_ty)] * arg_count
        func_type = ir.FunctionType(ir.PointerType(value_struct_ty), arg_types)
        func = ir.Function(module, func_type, name=self.name)
        block = func.append_basic_block(name="entry")
        func_builder = ir.IRBuilder(block)

        # Add parameters to symbol table
        for i, arg in enumerate(func.args):
            arg.name = arg_names[i]
            scoped_table[arg.name] = arg
            # Default initialization for boxed parameters
            if arg.type.pointee == value_struct_ty:
                ASTNode.box_int(func_builder, ir.Constant(ir.IntType(32), 0))

        # Codegen the function body.
        # Ignore return since ReturnNode will handle the return type.
        for node in self.children[1:]:
            node.codegen(func_builder, module, scoped_table)

        # If no explicit return is found, provide a default return value
        if not func_builder.block.is_terminated:
            default_boxed = ASTNode.box_int(func_builder, ir.Constant(ir.IntType(32), 0))
            func_builder.ret(default_boxed)

        return func

class FunctionCallNode(ASTNode):
    def __init__(self, token: Token):
        super().__init__(token)

    def codegen(self, builder, module, symbol_table):
        func = symbol_table.get(self.token.value)
        if func is None:
            raise CodeGenError(f"Undefined function: {self.token.value}")
        args = []
        param_types = func.function_type.args
        for i, arg in enumerate(self.children):
            val = arg.codegen(builder, module, symbol_table)
            expected_type = param_types[i] if i < len(param_types) else None
            # Only cast if param_types is long enough
            if self.token.value in NATIVE_FUNCS and self.is_boxed_value(val):
                val = self.unbox(val, builder, module)
            elif expected_type and self.token.value not in NATIVE_FUNCS and not self.is_boxed_value(val):
                val = self.box(val, builder)
            elif expected_type and val.type != expected_type:
                # Example: cast [N x i8]* to i8*
                if isinstance(expected_type, ir.PointerType) and expected_type.pointee == ir.IntType(8):
                    val = builder.bitcast(val, expected_type)
            args.append(val)
        return builder.call(func, args)

class BlockNode(ASTNode):
    def __init__(self, token: Token):
        super().__init__(token)

    def codegen(self, builder, module, symbol_table):
        result = None
        for stmt in self.children:
            result = stmt.codegen(builder, module, symbol_table)
        return result

class BinaryOpNode(ASTNode):
    def __init__(self, token: Token):
        super().__init__(token)

    @staticmethod
    def numeric_binop(builder, left, right, op_float, op_int, op_name):
        # Disallow string operands
        if ASTNode.is_string_value(left) or ASTNode.is_string_value(right):
            raise CodeGenError(f"Cannot {op_name} string values")
        # Promote to float if needed
        if left.type == ir.FloatType() or right.type == ir.FloatType():
            left = builder.sitofp(left, ir.FloatType()) if left.type != ir.FloatType() else left
            right = builder.sitofp(right, ir.FloatType()) if right.type != ir.FloatType() else right
            return op_float(left, right)
        # Require matching types
        if left.type != right.type:
            raise CodeGenError(f"Type mismatch in {op_name}: {left.type} vs {right.type}")
        return op_int(left, right)

    def codegen(self, builder, module, symbol_table):
        infix_op = self.token.type
        left = self.children[0].codegen(builder, module, symbol_table)
        right = self.children[1].codegen(builder, module, symbol_table)

        if ASTNode.is_boxed_value(left):
            left = ASTNode.unbox(left, builder, module)
        if ASTNode.is_boxed_value(right):
            right = ASTNode.unbox(right, builder, module)

        if infix_op == TokenType.PLUS:
            # String concatenation
            if (self.is_string_value(left) and self.is_string_value(right)):
                func = symbol_table.get("strcat")
                # Get pointers to the string data
                left_ptr = builder.bitcast(left, ir.PointerType(ir.IntType(8)))
                right_ptr = builder.bitcast(right, ir.PointerType(ir.IntType(8)))
                return builder.call(func, [left_ptr, right_ptr])
            return self.numeric_binop(builder, left, right, builder.fadd, builder.add, "add")
        elif infix_op == TokenType.MINUS:
            return self.numeric_binop(builder, left, right, builder.fsub, builder.sub, "subtract")
        elif infix_op == TokenType.SLASH:
            return self.numeric_binop(builder, left, right, builder.fdiv, builder.sdiv, "divide")
        elif infix_op == TokenType.STAR:
            return self.numeric_binop(builder, left, right, builder.fmul, builder.mul, "multiply")
        elif infix_op == TokenType.AND:
            return builder.and_(left, right)
        elif infix_op == TokenType.OR:
            return builder.or_(left, right)
        elif infix_op in (TokenType.EQUAL, TokenType.NOT_EQ, TokenType.LT_EQ, TokenType.LT, TokenType.GT_EQ, TokenType.GT):
            op = self.token.value
            if self.is_string_value(left) and self.is_string_value(right):
                func = symbol_table.get("strcmp")
                left_ptr = builder.bitcast(left, ir.PointerType(ir.IntType(8)))
                right_ptr = builder.bitcast(right, ir.PointerType(ir.IntType(8)))
                truthy =  builder.call(func, [left_ptr, right_ptr])
                return builder.icmp_signed(op, truthy, ir.Constant(ir.IntType(32), 0))
            elif left.type == ir.FloatType() or right.type == ir.FloatType():
                # Convert int to float if one side is float with other being int
                left = builder.sitofp(left, ir.FloatType()) if left.type != ir.FloatType() else left
                right = builder.sitofp(right, ir.FloatType()) if right.type != ir.FloatType() else right
                return builder.fcmp_ordered(op, left, right)
            elif left.type != right.type:
                raise CodeGenError(f"Type mismatch in comparison: {left.type} vs {right.type}")
            return builder.icmp_signed(op, left, right)
        raise CodeGenError(f"Unknown infix operator {infix_op}")

class ReturnNode(ASTNode):
    def __init__(self, token: Token):
        super().__init__(token)

    def codegen(self, builder, module, symbol_table):
        if not self.children:
            builder.ret(ir.Constant(ir.PointerType(value_struct_ty), None))
            return
        value_node = self.children[0]
        value = value_node.codegen(builder, module, symbol_table)
        # Always box the return value if not already boxed
        if not ASTNode.is_boxed_value(value):
            value = ASTNode.box(value, builder)
        builder.ret(value)

class IfNode(ASTNode):
    def __init__(self, token: Token):
        super().__init__(token)

    def codegen(self, builder, module, symbol_table):
        cond_value = self.children[0].codegen(builder, module, symbol_table)
        with builder.if_else(cond_value) as (then, otherwise):
            with then:
                self.children[1].codegen(builder, module, symbol_table)
            with otherwise:
                if len(self.children) > 2:
                    self.children[2].codegen(builder, module, symbol_table)

class WhileNode(ASTNode):
    def __init__(self, token: Token):
        super().__init__(token)

    def codegen(self, builder, module, symbol_table):
        pass

class PrefixNode(ASTNode):
    def __init__(self, token: Token):
        super().__init__(token)

    def operator(self) -> TokenType:
        return self.token.type

    def codegen(self, builder, module, symbol_table):
        raise CodeGenError("Prefix expressions are not implemented yet")

class LetNode(ASTNode):
    def __init__(self, token: Token):
        super().__init__(token)

    def codegen(self, builder: IRBuilder, module, symbol_table):
        identifier_node = self.children[0]
        value_node = self.children[1]
        value = value_node.codegen(builder, module, symbol_table)
        if value_node.token.type == TokenType.INT:
            var_addr = builder.alloca(ir.IntType(32), name=identifier_node.token.value)
            builder.store(value, var_addr)
        elif value_node.token.type == TokenType.FLOAT:
            var_addr = builder.alloca(ir.FloatType(), name=identifier_node.token.value)
            builder.store(value, var_addr)
        elif value_node.token.type == TokenType.FALSE or value_node.token.type == TokenType.TRUE:
            var_addr = builder.alloca(ir.IntType(1), name=identifier_node.token.value)
            builder.store(value, var_addr)
        elif value_node.token.type == TokenType.STRING:
            value.name = identifier_node.token.value
            var_addr = value
        elif value_node.token.type == TokenType.FUNCTION:
            var_addr = value
        else: # infix operations and IDENTIFIER token
            var_addr = builder.alloca(value.type, name=identifier_node.token.value)
            builder.store(value, var_addr)

            # Default initialization for boxed type if value is None and var_addr is a boxed pointer
        if value is None and hasattr(var_addr.type, 'pointee') and var_addr.type.pointee == value_struct_ty:
            ASTNode.box_int(builder, ir.Constant(ir.IntType(32), 0))

        symbol_table[identifier_node.token.value] = var_addr
        return var_addr
