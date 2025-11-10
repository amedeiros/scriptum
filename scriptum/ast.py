# type: ignore
from scriptum.lexer import Token, TokenType
from abc import ABC, abstractmethod
from llvmlite import ir
from llvmlite.ir.builder import IRBuilder
from llvmlite.ir.module import Module
from typing import Literal

# Array struct definition
vector_struct_ty = ir.LiteralStructType([
    ir.IntType(64),                  # type tag
    ir.PointerType(ir.IntType(8)),   # data pointer (opaque)
])

# Type tags
TYPE_INT = 0
TYPE_FLOAT = 1
TYPE_BOOL = 2
TYPE_STRING = 3
TYPE_ARRAY = 4

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

    def gentype(self) -> ir.Type:
        raise NotImplementedError("gentype not implemented for base ASTNode")

    def _gentype_from_token(self, static_type: TokenType) -> ir.Type:
        if static_type == TokenType.TYPE_INT:
            return ir.IntType(64)
        elif static_type == TokenType.TYPE_FLOAT:
            return ir.FloatType()
        elif static_type == TokenType.TYPE_STRING:
            return ir.PointerType(ir.IntType(8))
        elif static_type == TokenType.TYPE_BOOL:
            return ir.IntType(1)
        elif static_type == TokenType.TYPE_ARRAY:
            return ir.PointerType(vector_struct_ty)
        elif self.static_return_type == TokenType.TYPE_VOID:
            return ir.VoidType()
        
        return None

    @abstractmethod
    def codegen(self, builder: IRBuilder, module: Module, symbol_table: dict[str, ir.Value]):
        pass

    @staticmethod
    def is_string_value(val):
        return isinstance(val, ir.PointerType) and val.pointee == ir.IntType(8) or \
                (hasattr(val, 'type') and isinstance(val.type, ir.PointerType) and val.type.pointee == ir.IntType(8))

class NumberNode(ASTNode):
    def __init__(self, token: Token):
        super().__init__(token)

    def gentype(self) -> ir.Type:
        if self.token.type == TokenType.INT:
            return ir.IntType(64)
        elif self.token.type == TokenType.FLOAT:
            return ir.FloatType()

        raise CodeGenError(f"Unknown number type {self.token.type}")

    def codegen(self, builder, module, symbol_table):
        if self.token.type == TokenType.INT:
            return ir.Constant(ir.IntType(64), self.token.value)
        elif self.token.type == TokenType.FLOAT:
            return ir.Constant(ir.FloatType(), self.token.value)
        
        raise CodeGenError(f"Unknown number type {self.token.type}")
    
class SubscriptNode(ASTNode):
    static_type: ir.Type

    def codegen(self, builder, module, symbol_table):
        base_node = self.children[0]
        index_node = self.children[1]

        # Generate code for the base array and index
        array_ptr = base_node.codegen(builder, module, symbol_table)
        index = index_node.codegen(builder, module, symbol_table)

        # Determine the static type of the array elements
        self.static_type = base_node.static_type
        if self.static_type is None and base_node.token.type == TokenType.IDENTIFIER:
            self.static_type = symbol_table.get(f"{base_node.token.value}_type")
        if self.static_type is None:
            raise CodeGenError("Cannot subscript array with unknown element type")

        # Select the appropriate get function based on the static type
        get_array_func = None
        if self.static_type == ir.IntType(64):
            get_array_func = symbol_table["int_array_get"]
        elif self.static_type == ir.FloatType():
            get_array_func = symbol_table["float_array_get"]
        elif self.static_type == ir.IntType(1):
            get_array_func = symbol_table["bool_array_get"]
        elif isinstance(self.static_type, ir.PointerType) and \
             self.static_type.pointee == ir.IntType(8):
            get_array_func = symbol_table["string_array_get"]
        else:
            raise CodeGenError(f"Unsupported array element type for subscripting: {self.static_type}")

        result = builder.call(get_array_func, [array_ptr, index])
        value = builder.bitcast(result, self.static_type)
        return value

class ArrayLiteralNode(ASTNode):
    def __init__(self, token: Token):
        super().__init__(token)
        self.static_type = None

    def codegen(self, builder, module, symbol_table):
        if len(self.children) == 0 and self.static_type is None:
            raise CodeGenError("Cannot infer type of empty array literal")
        elif len(self.children) == 0:
            # Empty array, return a null pointer
            create_array_func = symbol_table["create_generic_array"]
            return builder.call(create_array_func, [ir.Constant(self.static_type, 0)])

        # Generate code for each element
        elem_values = [child.codegen(builder, module, symbol_table) for child in self.children]
        elem_type = elem_values[0].type
        self.static_type = elem_type  # Store for subscripting

        # Select the appropriate create and set functions based on element type
        create_array_func = None
        array_set_func = None
        if elem_type == ir.IntType(64):
            create_array_func = symbol_table["create_int_array"]
            array_set_func = symbol_table["int_array_set"]
        elif elem_type == ir.FloatType():
            create_array_func = symbol_table["create_float_array"]
            array_set_func = symbol_table["float_array_set"]
        elif elem_type == ir.IntType(1):
            create_array_func = symbol_table["create_bool_array"]
            array_set_func = symbol_table["bool_array_set"]
        elif isinstance(elem_type, ir.PointerType) and \
             elem_type.pointee == ir.IntType(8):
            create_array_func = symbol_table["create_string_array"]
            array_set_func = symbol_table["string_array_set"]
        else:
            breakpoint()
            raise CodeGenError(f"Unsupported array element type: {elem_type}")

        # Create the array
        vector_struct_ptr = builder.call(create_array_func, [ir.Constant(ir.IntType(64), len(elem_values))])
        # Initialize the array elements
        for i, val in enumerate(elem_values):
            index = ir.Constant(ir.IntType(64), i)
            casted_val = builder.bitcast(val, self.static_type)
            builder.call(array_set_func, [vector_struct_ptr, index, casted_val])
        
        return vector_struct_ptr

class StringNode(ASTNode):
    def __init__(self, token: Token):
        super().__init__(token)

    def gentype(self) -> ir.Type:
        return ir.PointerType(ir.IntType(8))

    def codegen(self, builder, module, symbol_table):
        str_bytes = bytearray(self.token.value.encode("utf8")) + b"\00"
        str_type = ir.ArrayType(ir.IntType(8), len(str_bytes))
        local_str = builder.alloca(str_type)
        self.type = ir.PointerType(str_type)
        # Store each byte (could use a loop or memcpy for efficiency)
        for i, b in enumerate(str_bytes):
            idx = ir.Constant(ir.IntType(32), i)
            ptr = builder.gep(local_str, [ir.Constant(ir.IntType(32), 0), idx])
            builder.store(ir.Constant(ir.IntType(8), b), ptr)
        
        return builder.bitcast(local_str, ir.PointerType(ir.IntType(8)))
        # return local_str

class BooleanNode(ASTNode):
    def __init__(self, token: Token, value: bool):
        super().__init__(token)
        self.value = value

    def gentype(self) -> ir.Type:
        return ir.IntType(1)

    def codegen(self, builder, module, symbol_table):
        return ir.Constant(ir.IntType(1), 1 if self.value else 0)

class IdentifierNode(ASTNode):
    static_type: Literal[TokenType.TYPE_INT, TokenType.TYPE_FLOAT,
                         TokenType.TYPE_STRING, TokenType.TYPE_BOOL,
                         TokenType.TYPE_ARRAY, TokenType.TYPE_CALLABLE]
    array_elem_type: ir.Type | None

    def __init__(self, token: Token):
        super().__init__(token)
        self.static_type = None

    def gentype(self) -> ir.Type:
        type = self._gentype_from_token(self.static_type)
        if type:
            return type

        raise CodeGenError(f"Unknown static type for identifier {self.token.value}")

    def codegen(self, builder, module, symbol_table):
        var_addr = symbol_table.get(self.token.value)
        if var_addr is None:
            raise CodeGenError(f"Undefined variable: {self.token.value}")
        
        # If function return
        if isinstance(var_addr, ir.Function):
            return var_addr

        # If the variable is a string/array return its pointer
        if ASTNode.is_string_value(var_addr) or \
            (isinstance(var_addr.type, ir.types.PointerType) and var_addr.type.pointee == vector_struct_ty):
            return var_addr
        # Only load if it's a pointer to a non-array type
        if isinstance(var_addr.type, ir.types.PointerType):
            return builder.load(var_addr)
        # Otherwise return the loaded value
        return var_addr


class ArgumentIdentifierNode(IdentifierNode):
    static_type: Literal[TokenType.TYPE_INT, TokenType.TYPE_FLOAT,
                         TokenType.TYPE_STRING, TokenType.TYPE_BOOL,
                         TokenType.TYPE_ARRAY, TokenType.TYPE_CALLABLE]
    callable_arg_types: list[Literal[TokenType.TYPE_INT, TokenType.TYPE_FLOAT,
                                     TokenType.TYPE_STRING, TokenType.TYPE_BOOL,
                                     TokenType.TYPE_ARRAY, TokenType.TYPE_CALLABLE]]
    callable_return_type: ir.Type

    def __init__(self, token: Token, static_type, callable_arg_types=[], callable_return_type=TokenType.TYPE_VOID):
        super().__init__(token)
        self.static_type = static_type
        self.callable_arg_types = callable_arg_types
        self.callable_return_type = callable_return_type

    def gentype(self) -> ir.Type:
        if self.static_type == TokenType.TYPE_CALLABLE:
            return_type = self._gentype_from_token(self.callable_return_type)
            arg_types = [self._gentype_from_token(t) for t in self.callable_arg_types]
            return ir.PointerType(ir.FunctionType(return_type, arg_types))
        return self._gentype_from_token(self.static_type)

class FunctionNode(ASTNode):
    static_return_type: Literal[TokenType.TYPE_INT, TokenType.TYPE_FLOAT,
                                TokenType.TYPE_STRING, TokenType.TYPE_BOOL,
                                TokenType.TYPE_ARRAY, TokenType.TYPE_VOID]

    def __init__(self, token: Token, name=None):
        super().__init__(token)
        self.name = name
        self.static_return_type = TokenType.TYPE_VOID

    def gentype(self) -> ir.Type:
        type = self._gentype_from_token(self.static_return_type)
        if type:
            return type
        raise CodeGenError(f"Unknown static return type for function {self.name}")

    def codegen(self, builder, module, symbol_table):
        scoped_table = SymbolTable(parent=symbol_table)
        args = self.children[0]
        arg_names = [arg.token.value for arg in args]
        arg_types = [arg.gentype() for arg in args]
        # First part is the return type
        func_type = ir.FunctionType(self.gentype(), arg_types)
        func = ir.Function(module, func_type, name=self.name)
        block = func.append_basic_block(name="entry")
        func_builder = ir.IRBuilder(block)

         # Add the function itself to the scoped symbol table for recursion
        scoped_table[self.name] = func

        # Add parameters to symbol table
        for i, arg in enumerate(func.args):
            arg.name = arg_names[i]
            scoped_table[arg.name] = arg

        # Codegen the function body.
        for node in self.children[1:]:
            node.codegen(func_builder, module, scoped_table)

        # If no explicit return is found, provide a default return value
        if not func_builder.block.is_terminated:
            func_builder.ret_void()

        return func

class AppendNode(ASTNode):
    def codegen(self, builder, module, symbol_table):
        array_node = self.children[0]
        value_node = self.children[1]
        array_ptr = array_node.codegen(builder, module, symbol_table)
        value = value_node.codegen(builder, module, symbol_table)

        # We want the static type of the array elements not the value passed.
        if array_node.token.type == TokenType.IDENTIFIER:
            static_type = symbol_table.get(f"{array_node.token.value}_type")
        else:
            breakpoint()
            static_type = array_node.children[0].gentype()

        if static_type is None:
            breakpoint()
            raise CodeGenError(f"Cannot determine static type of array for append: {array_node.token.value}")

        append_func = None
        # static_type = value.type
        if static_type == ir.IntType(64):
            append_func = symbol_table["int_array_push_back"]
        elif static_type == ir.FloatType():
            append_func = symbol_table["float_array_push_back"]
        elif static_type == ir.IntType(1):
            append_func = symbol_table["bool_array_push_back"]
        elif ASTNode.is_string_value(static_type):
            append_func = symbol_table["string_array_push_back"]
        else:
            raise CodeGenError(f"Unsupported array element type for append: {static_type}")

        # Validate arg matches
        if value.type != static_type:
            raise CodeGenError(f"Type mismatch in append: array element type {static_type} vs value type {value.type}")

        builder.call(append_func, [array_ptr, value])

class FunctionCallNode(ASTNode):
    def __init__(self, token: Token):
        super().__init__(token)

    def codegen(self, builder, module, symbol_table):
        func = symbol_table.get(self.token.value)
        if func is None:
            raise CodeGenError(f"Undefined function: {self.token.value}")
        args = []
        for arg in self.children:
            val = arg.codegen(builder, module, symbol_table)
            args.append(val)
        try:
            _args = args
            return builder.call(func, args)
        except Exception as e:
            breakpoint()
            raise CodeGenError(f"Error calling function {self.token.value}: {e}")

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

        if infix_op == TokenType.PLUS:
            # String concatenation
            if (ASTNode.is_string_value(left) and ASTNode.is_string_value(right)):
                strlen_func = symbol_table.get("strlen")
                strcpy_func = symbol_table.get("strcpy")
                strcat_func = symbol_table.get("strcat")
                malloc_func = symbol_table.get("malloc")
                left_ptr = builder.bitcast(left, ir.PointerType(ir.IntType(8)))
                right_ptr = builder.bitcast(right, ir.PointerType(ir.IntType(8)))
                left_len = builder.call(strlen_func, [left_ptr])
                right_len = builder.call(strlen_func, [right_ptr])
                total_len = builder.add(left_len, right_len)
                total_len = builder.zext(total_len, ir.IntType(64))
                total_len_plus1 = builder.add(total_len, ir.Constant(ir.IntType(64), 1))
                buf_ptr = builder.call(malloc_func, [total_len_plus1])
                buf_ptr = builder.bitcast(buf_ptr, ir.PointerType(ir.IntType(8)))
                builder.call(strcpy_func, [buf_ptr, left_ptr])
                builder.call(strcat_func, [buf_ptr, right_ptr])
                return buf_ptr
            return self.numeric_binop(builder, left, right, builder.fadd, builder.add, "add")
        elif infix_op == TokenType.MINUS:
            return self.numeric_binop(builder, left, right, builder.fsub, builder.sub, "subtract")
        elif infix_op == TokenType.SLASH:
            return self.numeric_binop(builder, left, right, builder.fdiv, builder.sdiv, "divide")
        elif infix_op == TokenType.STAR:
            return self.numeric_binop(builder, left, right, builder.fmul, builder.mul, "multiply")
        elif infix_op == TokenType.AND:
            if left.type != ir.IntType(1):
                left = builder.trunc(left, ir.IntType(1))
            if right.type != ir.IntType(1):
                right = builder.trunc(right, ir.IntType(1))
            return builder.and_(left, right)
        elif infix_op == TokenType.OR:
            if left.type != ir.IntType(1):
                left = builder.trunc(left, ir.IntType(1))
            if right.type != ir.IntType(1):
                right = builder.trunc(right, ir.IntType(1))
            return builder.or_(left, right)
        elif infix_op in (TokenType.EQUAL, TokenType.NOT_EQ, TokenType.LT_EQ, TokenType.LT, TokenType.GT_EQ, TokenType.GT):
            op = self.token.value
            if ASTNode.is_string_value(left) and ASTNode.is_string_value(right):
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
        if self.children:
            value_node = self.children[0]
            value = value_node.codegen(builder, module, symbol_table)
            builder.ret(value)
        else: # empty return
            builder.ret_void()

class IfNode(ASTNode):
    def __init__(self, token: Token):
        super().__init__(token)

    def codegen(self, builder, module, symbol_table):
        cond_value = self.children[0].codegen(builder, module, symbol_table)
        if cond_value.type != ir.IntType(1):
            cond_value = builder.trunc(cond_value, ir.IntType(1))

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
        cond_block = builder.append_basic_block("while.cond")
        body_block = builder.append_basic_block("while.body")
        after_block = builder.append_basic_block("while.after")

        builder.branch(cond_block)

        # Condition block
        builder.position_at_start(cond_block)
        cond_value = self.children[0].codegen(builder, module, symbol_table)
        if cond_value.type != ir.IntType(1):
            cond_value = builder.trunc(cond_value, ir.IntType(1))
        builder.cbranch(cond_value, body_block, after_block)

        # Body block
        builder.position_at_start(body_block)
        self.children[1].codegen(builder, module, symbol_table)
        builder.branch(cond_block)

        # After loop block
        builder.position_at_start(after_block)

class PrefixNode(ASTNode):
    def __init__(self, token: Token):
        super().__init__(token)

    def operator(self) -> TokenType:
        return self.token.type

    def codegen(self, builder, module, symbol_table):
        raise CodeGenError("Prefix expressions are not implemented yet")


class AssignNode(ASTNode):
    def __init__(self, token: Token):
        super().__init__(token)

    def codegen(self, builder: IRBuilder, module, symbol_table):
        node = self.children[0]
        value_node = self.children[1]

        if node.token.type == TokenType.IDENTIFIER:
            var_addr = symbol_table.get(node.token.value)
            value = value_node.codegen(builder, module, symbol_table)
            builder.store(value, var_addr)
        elif node.token.type == TokenType.LBRACK: # Subscript assignment
            subscript_node = node
            base_node = subscript_node.children[0]
            index_node = subscript_node.children[1]

            # Generate code for the base array, index, and value
            array_ptr = base_node.codegen(builder, module, symbol_table)
            index = index_node.codegen(builder, module, symbol_table)
            value = value_node.codegen(builder, module, symbol_table)
            static_type = value.type

            # Select the appropriate set function based on the static type
            set_array_func = None
            if static_type == ir.IntType(64):
                set_array_func = symbol_table["int_array_set"]
            elif static_type == ir.FloatType():
                set_array_func = symbol_table["float_array_set"]
            elif static_type == ir.IntType(1):
                set_array_func = symbol_table["bool_array_set"]
            elif ASTNode.is_string_value(static_type):
                set_array_func = symbol_table["string_array_set"]
            else:
                raise CodeGenError(f"Unsupported array element type for assignment: {static_type}")

            # Call the set function
            builder.call(set_array_func, [array_ptr, index, value])
        else:
            raise CodeGenError("Invalid assignment target")


class LetNode(ASTNode):
    def __init__(self, token: Token):
        super().__init__(token)

    def codegen(self, builder: IRBuilder, module, symbol_table):
        identifier_node = self.children[0]
        value_node      = self.children[1]
        value           = value_node.codegen(builder, module, symbol_table)

        if identifier_node.token.type != TokenType.IDENTIFIER:
            raise CodeGenError("Invalid identifier")

        if value_node.token.type in (TokenType.STRING, TokenType.IDENTIFIER, TokenType.FUNCTION, TokenType.LBRACK):
            var_addr = value
        else: # INT, FLOAT, BOOL, infix operations, etc
            var_addr = builder.alloca(value.type)
            builder.store(value, var_addr)
        
        # During parsing we set the name on the FunctionNode for codegen.
        # This is because we need a unique name at the codegen site of a function (FunctionNode).
        if value_node.token.type != TokenType.FUNCTION:
            var_addr.name = identifier_node.token.value

        # We need to determine the static type of the identifier
        static_type = None
        if value_node.token.type == TokenType.LBRACK:
            identifier_node.static_type = TokenType.TYPE_ARRAY
            identifier_node.array_elem_type = value_node.static_type
            static_type = value_node.static_type
        elif value_node.token.type == TokenType.IDENTIFIER:
            identifier_node.static_type = symbol_table.get(f"{value_node.token.value}_type")
            static_type = identifier_node.static_type
        else:
            try:
                identifier_node.static_type = value_node.gentype()
                static_type = identifier_node.static_type
            except Exception as e:
                pass

        symbol_table[identifier_node.token.value] = var_addr
        symbol_table[f"{identifier_node.token.value}_type"] = static_type
        return var_addr
