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

def array_static_type_from_identifier(array_node, symbol_table):
    if array_node.token.type == TokenType.IDENTIFIER:
        return symbol_table.get(f"{array_node.token.value}").static_type
    return array_node.static_type

class SymbolEntry:
    def __init__(self, variable_addr, static_type=None, node=None):
        self.variable_addr = variable_addr
        self.static_type = static_type
        self.node = node


class SymbolTable(dict[str, SymbolEntry]):
    def __init__(self, parent: "SymbolTable" = None):
        super().__init__()
        self.parent = parent

    def __setitem__(self, key: str, value: SymbolEntry):
        super().__setitem__(key, value)

    def __getitem__(self, key: str) -> SymbolEntry:
        try:
            return super().__getitem__(key)
        except KeyError:
            if self.parent:
                return self.parent[key]
            raise CodeGenError(f"Undefined variable: {key}")
    
    def get(self, key: str) -> SymbolEntry | None:
        v = super().get(key)
        if v is None and self.parent:
            return self.parent.get(key)
        return v


class CodeGenError(Exception):
    pass


class ASTNode(ABC):
    token: Token
    children: list["ASTNode"]
    static_type = None

    def __init__(self, token: Token):
        self.token = token
        self.children = []

    def add_child(self, child: "ASTNode"):
        self.children.append(child)

    def mangled_name(self, symbol_table):
        context = symbol_table.get("__context__")
        name = self.token.value
        if context and "module_name" in context and not context.get("is_main", False):
            name = f"{context['module_name']}_{name}"

        return name

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
        elif static_type == TokenType.TYPE_VOID:
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

        raise CodeGenError(f"Unknown number type {self.token.type} at {self.token.line_number()}")

    def codegen(self, builder, module, symbol_table):
        if self.token.type == TokenType.INT:
            return ir.Constant(ir.IntType(64), self.token.value)
        elif self.token.type == TokenType.FLOAT:
            return ir.Constant(ir.FloatType(), self.token.value)
        
        raise CodeGenError(f"Unknown number type {self.token.type} at {self.token.line_number()}")
    
class DotNode(ASTNode):
    def codegen(self, builder: IRBuilder, module: Module, symbol_table: dict[str, any]):
        left = self.children[0]
        right = self.children[1]
        mangled_name = f"{left.token.value}_{right.token.value}"

        if isinstance(right, FunctionCallNode):
            func = symbol_table.get(mangled_name)
            namespace = symbol_table.get(left.token.value)
            # It might be an "as" alias
            if func is None and namespace is not None:
                mangled_name = right.mangled_name(namespace)
                func = namespace.get(mangled_name)
            if func is None:
                raise CodeGenError(f"Undefined function: {mangled_name} at {right.token.line_number()}")
            # Generate argument values
            arg_values = [child.codegen(builder, module, symbol_table) for child in right.children]
            return builder.call(func.variable_addr, arg_values)
        else:
            raise CodeGenError(f"DotNode only supports function calls currently at {self.token.line_number()}")

class SubscriptNode(ASTNode):
    static_type: ir.Type

    def codegen(self, builder, module, symbol_table):
        base_node = self.children[0]
        index_node = self.children[1]

        # Generate code for the base array and index
        array_ptr = base_node.codegen(builder, module, symbol_table)
        index = index_node.codegen(builder, module, symbol_table)

        # Determine the static type of the array elements
        self.static_type = array_static_type_from_identifier(base_node, symbol_table)
        if self.static_type is None:
            raise CodeGenError(f"Cannot subscript array with unknown element type at {self.token.line_number()}")

        # Select the appropriate get function based on the static type
        get_array_func = None
        if self.static_type == ir.IntType(64):
            get_array_func = symbol_table["int_array_get"].variable_addr
        elif self.static_type == ir.FloatType():
            get_array_func = symbol_table["float_array_get"].variable_addr
        elif self.static_type == ir.IntType(1):
            get_array_func = symbol_table["bool_array_get"].variable_addr
        elif ASTNode.is_string_value(self.static_type):
            get_array_func = symbol_table["string_array_get"].variable_addr
        elif self.static_type == ir.PointerType(vector_struct_ty):
            get_array_func = symbol_table["array_array_get"].variable_addr
        else:
            raise CodeGenError(f"Unsupported array element type for subscripting: {self.static_type} at {self.token.line_number()}")

        return builder.call(get_array_func, [array_ptr, index])

class ArrayReplicationNode(ASTNode):
    static_type: ir.Type

    def codegen(self, builder, module, symbol_table):
        array_node = self.children[0]
        count_node = self.children[1]

        # Generate value and count for array replication
        count = count_node.codegen(builder, module, symbol_table)
        val = array_node.children[0].codegen(builder, module, symbol_table)

        # Determine the static type of the array elements
        self.static_type = val.type
        # Select the appropriate create and set functions based on element type
        create_array_func = None
        if self.static_type == ir.IntType(64):
            create_array_func = symbol_table["create_int_array_from_value"].variable_addr
        elif self.static_type == ir.FloatType():
            create_array_func = symbol_table["create_float_array_from_value"].variable_addr
        elif self.static_type == ir.IntType(1):
            create_array_func = symbol_table["create_bool_array_from_value"].variable_addr
        elif ASTNode.is_string_value(self.static_type):
            create_array_func = symbol_table["create_string_array_from_value"].variable_addr
        elif self.static_type == ir.PointerType(vector_struct_ty):
            create_array_func = symbol_table["create_array_array_from_value"].variable_addr
        else:
            raise CodeGenError(f"Unsupported array element type for replication: {self.static_type} at {self.token.line_number()}")

        # Create the new replicated array
        vector_struct_ptr = builder.call(create_array_func, [val, count])
        
        return vector_struct_ptr

class ArrayLiteralNode(ASTNode):
    def __init__(self, token: Token):
        super().__init__(token)

    def codegen(self, builder, module, symbol_table):
        if len(self.children) == 0 and self.static_type is None:
            raise CodeGenError(f"Cannot infer type of empty array literal at {self.token.line_number()}")
        elif len(self.children) == 0:
            # Not supported right now.
            raise CodeGenError(f"Cannot create empty array literal without a known static type at {self.token.line_number()}")

        # Generate code for each element
        elem_values = [child.codegen(builder, module, symbol_table) for child in self.children]
        elem_type = elem_values[0].type
        self.static_type = elem_type  # Store for subscripting

        # Select the appropriate create and set functions based on element type
        create_array_func = None
        array_set_func = None
        if elem_type == ir.IntType(64):
            create_array_func = symbol_table["create_int_array"].variable_addr
            array_set_func = symbol_table["int_array_set"].variable_addr
        elif elem_type == ir.FloatType():
            create_array_func = symbol_table["create_float_array"].variable_addr
            array_set_func = symbol_table["float_array_set"].variable_addr
        elif elem_type == ir.IntType(1):
            create_array_func = symbol_table["create_bool_array"].variable_addr
            array_set_func = symbol_table["bool_array_set"].variable_addr
        elif ASTNode.is_string_value(elem_type):
            create_array_func = symbol_table["create_string_array"].variable_addr
            array_set_func = symbol_table["string_array_set"].variable_addr
        elif elem_type == ir.PointerType(vector_struct_ty):
            create_array_func = symbol_table["create_array_array"].variable_addr
            array_set_func = symbol_table["array_array_set"].variable_addr
        else:
            raise CodeGenError(f"Unsupported array element type: {elem_type} at {self.token.line_number()}")

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

        raise CodeGenError(f"Unknown static type for identifier {self.token.value} at {self.token.line_number()}")

    def codegen(self, builder, module, symbol_table):
        var_addr = symbol_table.get(self.token.value)
        if var_addr is None:
            raise CodeGenError(f"Undefined variable: {self.token.value} at {self.token.line_number()}")
        else:
            var_addr = var_addr.variable_addr
        
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
    default_value: ASTNode | None

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
        raise CodeGenError(f"Unknown static return type for function {self.name} at {self.token.line_number()}")

    def mangled_name(self, symbol_table):
        context = symbol_table.get("__context__")
        func_name = self.name
        if context and "module_name" in context and not context.get("is_main", False):
            func_name = f"{context["module_name"]}_{self.name}"

        return func_name

    def codegen(self, builder, module, symbol_table):
        scoped_table = SymbolTable(parent=symbol_table)
        args = self.children[0]
        arg_names = [arg.token.value for arg in args]
        arg_types = [arg.gentype() for arg in args]
        # First part is the return type
        func_type = ir.FunctionType(self.gentype(), arg_types)
        func = ir.Function(module, func_type, name=self.mangled_name(scoped_table))
        block = func.append_basic_block(name="entry")
        func_builder = ir.IRBuilder(block)

        # Add the function itself to the scoped symbol table for recursion
        scoped_table[self.mangled_name(scoped_table)] = SymbolEntry(variable_addr=func, static_type=self.gentype(), node=self)

        # Add parameters to symbol table
        for i, arg in enumerate(func.args):
            arg.name = arg_names[i]
            static_type = None
            # If the argument is an array, store its element type
            if args[i].static_type == TokenType.TYPE_ARRAY:
                static_type = self._gentype_from_token(args[i].callable_arg_types[0])
            else:
                static_type = self._gentype_from_token(args[i].static_type)
            # Create a local variable for the argument and store the value
            if isinstance(arg.type, ir.types.PointerType):
                local_ptr = arg
            else:
                local_ptr = func_builder.alloca(arg.type, name=arg.name)
                func_builder.store(arg, local_ptr)
            # Add the argument to the symbol table
            scoped_table[arg.name] = SymbolEntry(local_ptr, static_type, args[i])

        # Codegen the function body.
        for node in self.children[1:]:
            node.codegen(func_builder, module, scoped_table)

        # If no explicit return is found, provide a default return value
        if not func_builder.block.is_terminated:
            func_builder.ret_void()

        return func
    
class ArrayRemoveNode(ASTNode):
    def codegen(self, builder: IRBuilder, module: Module, symbol_table: dict[str, any]):
        array_node = self.children[0]
        index_node = self.children[1]
        array_ptr = array_node.codegen(builder, module, symbol_table)
        index = index_node.codegen(builder, module, symbol_table)

        # We want the static type of the array elements not the value passed.
        static_type = array_static_type_from_identifier(array_node, symbol_table)
        if static_type is None:
            raise CodeGenError(f"Cannot determine static type of array for append: {array_node.token.value} at {self.token.line_number()}")
        
        remove_func = None
        if static_type == ir.IntType(64):
            remove_func = symbol_table["int_array_remove"].variable_addr
        elif static_type == ir.FloatType():
            remove_func = symbol_table["float_array_remove"].variable_addr
        elif static_type == ir.IntType(1):
            remove_func = symbol_table["bool_array_remove"].variable_addr
        elif static_type == ir.PointerType(vector_struct_ty):
            remove_func = symbol_table["array_array_remove"].variable_addr
        elif ASTNode.is_string_value(static_type):
            remove_func = symbol_table["string_array_remove"].variable_addr
        else:
            raise CodeGenError(f"Unsupported array element type for remove: {static_type} at {self.token.line_number()}")
        
        return builder.call(remove_func, [array_ptr, index])

class ArrayIndexOfNode(ASTNode):
    def codegen(self, builder: IRBuilder, module: Module, symbol_table: dict[str, any]):
        array_node = self.children[0]
        value_node = self.children[1]
        array_ptr = array_node.codegen(builder, module, symbol_table)
        value = value_node.codegen(builder, module, symbol_table)

        # We want the static type of the array elements not the value passed.
        static_type = array_static_type_from_identifier(array_node, symbol_table)
        if static_type is None:
            raise CodeGenError(f"Cannot determine static type of array for index_of: {array_node.token.value} at {self.token.line_number()}")

        index_of_func = None
        if static_type == ir.IntType(64):
            index_of_func = symbol_table["int_array_index_of"].variable_addr
        elif static_type == ir.FloatType():
            index_of_func = symbol_table["float_array_index_of"].variable_addr
        elif static_type == ir.IntType(1):
            index_of_func = symbol_table["bool_array_index_of"].variable_addr
        elif static_type == ir.PointerType(vector_struct_ty):
            index_of_func = symbol_table["array_array_index_of"].variable_addr
        elif ASTNode.is_string_value(static_type):
            index_of_func = symbol_table["string_array_index_of"].variable_addr
        else:
            raise CodeGenError(f"Unsupported array element type for index_of: {static_type} at {self.token.line_number()}")

        return builder.call(index_of_func, [array_ptr, value])

class ArrayInsertNode(ASTNode):
    def codegen(self, builder: IRBuilder, module: Module, symbol_table: dict[str, any]):
        array_node = self.children[0]
        index_node = self.children[1]
        value_node = self.children[2]
        array_ptr = array_node.codegen(builder, module, symbol_table)
        index = index_node.codegen(builder, module, symbol_table)
        value = value_node.codegen(builder, module, symbol_table)

        # We want the static type of the array elements not the value passed.
        static_type = array_static_type_from_identifier(array_node, symbol_table)
        if static_type is None:
            raise CodeGenError(f"Cannot determine static type of array for insert: {array_node.token.value} at {self.token.line_number()}")
        
        insert_func = None
        if static_type == ir.IntType(64):
            insert_func = symbol_table["int_array_insert"].variable_addr
        elif static_type == ir.FloatType():
            insert_func = symbol_table["float_array_insert"].variable_addr
        elif static_type == ir.IntType(1):
            insert_func = symbol_table["bool_array_insert"].variable_addr
        elif static_type == ir.PointerType(vector_struct_ty):
            insert_func = symbol_table["array_array_insert"].variable_addr
        elif ASTNode.is_string_value(static_type):
            insert_func = symbol_table["string_array_insert"].variable_addr
        else:
            raise CodeGenError(f"Unsupported array element type for insert: {static_type} at {self.token.line_number()}")
        
        builder.call(insert_func, [array_ptr, index, value])

class ArrayPopNode(ASTNode):
    def codegen(self, builder: IRBuilder, module: Module, symbol_table: dict[str, any]):
        array_node = self.children[0]
        array_ptr = array_node.codegen(builder, module, symbol_table)

        # We want the static type of the array elements not the value passed.
        static_type = array_static_type_from_identifier(array_node, symbol_table)
        if static_type is None:
            raise CodeGenError(f"Cannot determine static type of array for pop: {array_node.token.value} at {self.token.line_number()}")
        
        pop_func = None
        if static_type == ir.IntType(64):
            pop_func = symbol_table["int_array_pop"].variable_addr
        elif static_type == ir.FloatType():
            pop_func = symbol_table["float_array_pop"].variable_addr
        elif static_type == ir.IntType(1):
            pop_func = symbol_table["bool_array_pop"].variable_addr
        elif static_type == ir.PointerType(vector_struct_ty):
            pop_func = symbol_table["array_array_pop"].variable_addr
        elif ASTNode.is_string_value(static_type):
            pop_func = symbol_table["string_array_pop"].variable_addr
        else:
            raise CodeGenError(f"Unsupported array element type for pop: {static_type} at {self.token.line_number()}")
        
        return builder.call(pop_func, [array_ptr])

class AppendNode(ASTNode):
    def codegen(self, builder, module, symbol_table):
        array_node = self.children[0]
        value_node = self.children[1]
        array_ptr = array_node.codegen(builder, module, symbol_table)
        value = value_node.codegen(builder, module, symbol_table)

        # We want the static type of the array elements not the value passed.
        static_type = array_static_type_from_identifier(array_node, symbol_table)
        if static_type is None:
            raise CodeGenError(f"Cannot determine static type of array for append: {array_node.token.value} at {self.token.line_number()}")

        append_func = None
        if static_type == ir.IntType(64):
            append_func = symbol_table["int_array_push_back"].variable_addr
        elif static_type == ir.FloatType():
            append_func = symbol_table["float_array_push_back"].variable_addr
        elif static_type == ir.IntType(1):
            append_func = symbol_table["bool_array_push_back"].variable_addr
        elif static_type == ir.PointerType(vector_struct_ty):
            append_func = symbol_table["array_array_push_back"].variable_addr
        elif ASTNode.is_string_value(static_type):
            append_func = symbol_table["string_array_push_back"].variable_addr
        else:
            raise CodeGenError(f"Unsupported array element type for append: {static_type} at {self.token.line_number()}")

        # Validate arg matches
        if value.type != static_type:
            raise CodeGenError(f"Type mismatch in append: array element type {static_type} vs value type {value.type} at {self.token.line_number()}")

        builder.call(append_func, [array_ptr, value])

class FunctionCallNode(ASTNode):
    def __init__(self, token: Token):
        super().__init__(token)

    def codegen(self, builder, module, symbol_table):
        func_name = self.token.value
        symbol_entry = symbol_table.get(func_name)
        if symbol_entry is None:
            raise CodeGenError(f"Undefined function: {func_name} {self.token.line_number()} at {self.token.line_number()}")

        # Get arguments
        func = symbol_entry.variable_addr
        args = []
        # Function being called was an argument to another function so we need the pointer to the function type instead of the function itself
        if symbol_entry.node and symbol_entry.node.static_type == TokenType.TYPE_CALLABLE:
            # Load it
            params = func.type.pointee.args
            var_arg_func = func.type.pointee.var_arg
        else: # Regular function
            params = func.args
            var_arg_func = func.ftype.var_arg

        param_len = len(params)
        arg_len = len(self.children)

        if not var_arg_func and param_len < arg_len:
            raise CodeGenError(f"Too many arguments provided for function {func_name}: expected {param_len}, got {arg_len} in {self.token.line_number()}")

        if param_len > arg_len:
            # Check for default values
            node_arguments = symbol_entry.node.children[0]
            for i in range(len(node_arguments)):
                if self.children and i < arg_len:
                    arg = self.children[i]
                    val = arg.codegen(builder, module, symbol_table)
                    args.append(val)
                else:
                    arg_node = node_arguments[i]
                    if isinstance(arg_node, ArgumentIdentifierNode) and arg_node.default_value is not None:
                        val = arg_node.default_value.codegen(builder, module, symbol_table)
                        args.append(val)
                    else:
                        raise CodeGenError(f"Missing argument {arg_node.token.value} for function {func_name} and no default value provided at {self.token.line_number()}")
        else:
            for arg in self.children:
                val = arg.codegen(builder, module, symbol_table)
                args.append(val)

        try:
            return builder.call(func, args)
        except Exception as e:
            _args = args
            breakpoint()
            raise CodeGenError(f"Error calling function {self.token.value}: {e} with arguments {args} at {self.token.line_number()}")

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

    def numeric_binop(self, builder, left, right, op_float, op_int, op_name):
        # Disallow string operands
        if ASTNode.is_string_value(left) or ASTNode.is_string_value(right):
            raise CodeGenError(f"Cannot {op_name} string values at {self.token.line_number()}")
        # Promote to float if needed
        if left.type == ir.FloatType() or right.type == ir.FloatType():
            left = builder.sitofp(left, ir.FloatType()) if left.type != ir.FloatType() else left
            right = builder.sitofp(right, ir.FloatType()) if right.type != ir.FloatType() else right
            return op_float(left, right)
        # Require matching types
        if left.type != right.type:
            raise CodeGenError(f"Type mismatch in {op_name}: {left.type} vs {right.type} at {self.token.line_number()}")
        return op_int(left, right)

    def codegen(self, builder, module, symbol_table):
        infix_op = self.token.type
        left = self.children[0].codegen(builder, module, symbol_table)
        right = self.children[1].codegen(builder, module, symbol_table)

        if infix_op == TokenType.PLUS:
            # String concatenation
            if (ASTNode.is_string_value(left) and ASTNode.is_string_value(right)):
                strlen_func = symbol_table.get("strlen").variable_addr
                strcpy_func = symbol_table.get("strcpy").variable_addr
                strcat_func = symbol_table.get("strcat").variable_addr
                malloc_func = symbol_table.get("malloc").variable_addr
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
                func = symbol_table.get("strcmp").variable_addr
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
                raise CodeGenError(f"Type mismatch in comparison: {left.type} vs {right.type} at {self.token.line_number()}")
            return builder.icmp_signed(op, left, right)
        raise CodeGenError(f"Unknown infix operator {infix_op} at {self.token.line_number()}")

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
            var_addr = symbol_table.get(node.token.value).variable_addr
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
                set_array_func = symbol_table["int_array_set"].variable_addr
            elif static_type == ir.FloatType():
                set_array_func = symbol_table["float_array_set"].variable_addr
            elif static_type == ir.IntType(1):
                set_array_func = symbol_table["bool_array_set"].variable_addr
            elif ASTNode.is_string_value(static_type):
                set_array_func = symbol_table["string_array_set"].variable_addr
            else:
                raise CodeGenError(f"Unsupported array element type for assignment: {static_type} at {self.token.line_number()}")

            # Call the set function
            builder.call(set_array_func, [array_ptr, index, value])
        else:
            raise CodeGenError(f"Invalid assignment target at {self.token.line_number()}")


class ForeignNode(ASTNode):
    static_return_type: Literal[TokenType.TYPE_INT, TokenType.TYPE_FLOAT,
                                TokenType.TYPE_STRING, TokenType.TYPE_BOOL,
                                TokenType.TYPE_ARRAY, TokenType.TYPE_VOID]
    identifier: Token | None
    name: str | None

    def __init__(self, token: Token):
        super().__init__(token)
        self.name = None
        self.identifier = None
        self.static_return_type = TokenType.TYPE_VOID

    def gentype(self) -> ir.Type:
        type = self._gentype_from_token(self.static_return_type)
        if type:
            return type
        raise CodeGenError(f"Unknown static return type for foreign function {self.name} at {self.token.line_number()}")

    def codegen(self, builder, module, symbol_table):
        identifier = self.identifier.token.value
        if identifier in symbol_table:
            raise CodeGenError(f"Symbol {identifier} already defined in the current scope at {self.token.line_number()}")

        var_arg = False
        arg_types = []
        for arg in self.children:
            # we parse this as a default value in the function parsing "var_arg = true" and we can check for it here
            if arg.token.value == "var_arg" and arg.default_value.token.value == "true":
                var_arg = True
            else:
                arg_types.append(arg.gentype())

        func_type = ir.FunctionType(self.gentype(), arg_types, var_arg=var_arg)
        func = ir.Function(module, func_type, name=identifier)
        symbol_table[identifier] = SymbolEntry(variable_addr=func, static_type=func_type, node=self)


class LetNode(ASTNode):
    def __init__(self, token: Token):
        super().__init__(token)

    def codegen(self, builder: IRBuilder, module, symbol_table):
        identifier_node = self.children[0]
        value_node      = self.children[1]
        value           = value_node.codegen(builder, module, symbol_table)

        if identifier_node.token.type != TokenType.IDENTIFIER:
            raise CodeGenError(f"Invalid identifier in let statement at {self.token.line_number()}")

        if isinstance(value, ir.PointerType) or value_node.token.type in (TokenType.STRING, TokenType.FUNCTION, TokenType.LBRACK):
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
            identifier_node.static_type = symbol_table.get(f"{value_node.token.value}").static_type
            static_type = identifier_node.static_type
        else:
            try:
                identifier_node.static_type = value_node.gentype()
                static_type = identifier_node.static_type
            except Exception:
                pass

        mangled_name = identifier_node.mangled_name(symbol_table)
        symbol_table[mangled_name] = SymbolEntry(var_addr, static_type, value_node)
        return var_addr

class ModuleIdentifierNode(ASTNode):
    def __init__(self, token: Token, module_as_name: Token | None = None):
        super().__init__(token)
        self.module_as_name = module_as_name

    def codegen(self, builder, module, symbol_table):
        # Module identifiers are handled at a higher level; nothing to do here.
        pass

class FromImportNode(ASTNode):
    def __init__(self, token: Token, module_name: Token):
        super().__init__(token)
        self.module_name = module_name

    def codegen(self, builder, module, symbol_table):
        # Module identifiers are handled at a higher level; nothing to do here.
        pass

class ImportNode(ASTNode):
    def codegen(self, builder, module, symbol_table):
        # Imports are handled at a higher level; nothing to do here.
        pass
