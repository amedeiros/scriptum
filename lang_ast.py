# type: ignore
from lexer import Token, TokenType
from abc import ABC, abstractmethod
from llvmlite import ir
from llvmlite.ir.builder import IRBuilder
from llvmlite.ir.module import Module


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
        local_str = builder.alloca(str_type)#, name="local_str")
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
        # If the variable is a string return its pointer
        # TODO: Handle other data types requiring a pointer
        if isinstance(var_addr.type, ir.types.PointerType) and \
            isinstance(var_addr.type.pointee, ir.types.ArrayType) and \
                var_addr.type.pointee.element == ir.IntType(8):
            return var_addr
        # Otherwise return the loaded value
        return builder.load(var_addr)

class FunctionNode(ASTNode):
    def __init__(self, token: Token):
        super().__init__(token)

    def codegen(self, builder, module, symbol_table):
        pass

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
            # Only cast if param_types is long enough
            if i < len(param_types):
                expected_type = param_types[i]
                if val.type != expected_type:
                    # Example: cast [N x i8]* to i8*
                    if isinstance(expected_type, ir.PointerType) and expected_type.pointee == ir.IntType(8):
                        val = builder.bitcast(val, expected_type)
            args.append(val)
        # _args = [arg.codegen(builder, module, symbol_table) for arg in self.children]
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

    def codegen(self, builder, module, symbol_table):
        infix_op = self.token.type
        left = self.children[0].codegen(builder, module, symbol_table)
        right = self.children[1].codegen(builder, module, symbol_table)
        if infix_op == TokenType.PLUS:
            # String concatination
            if (isinstance(left.type, ir.types.PointerType) and
                isinstance(left.type.pointee, ir.types.ArrayType)) or \
                (isinstance(right.type, ir.types.PointerType) and
                isinstance(right.type.pointee, ir.types.ArrayType)):
                func = symbol_table.get("strcat")
                left_ptr = builder.bitcast(left, ir.PointerType(ir.IntType(8)))
                right_ptr = builder.bitcast(right, ir.PointerType(ir.IntType(8)))
                return builder.call(func, [left_ptr, right_ptr])
            if left.type == ir.FloatType() or right.type == ir.FloatType():
                # Convert int to float if one side is float with other being int
                left = builder.sitofp(left, ir.FloatType()) if left.type != ir.FloatType() else left
                right = builder.sitofp(right, ir.FloatType()) if right.type != ir.FloatType() else right
                return builder.fadd(left, right)
            return builder.add(left, right)
        elif infix_op == TokenType.MINUS:
            return builder.sub(left, right)
        elif infix_op == TokenType.SLASH:
            if left.type == ir.FloatType() or right.type == ir.FloatType():
                # Convert int to float if one side is float with other being int
                left = builder.sitofp(left, ir.FloatType()) if left.type != ir.FloatType() else left
                right = builder.sitofp(right, ir.FloatType()) if right.type != ir.FloatType() else right
                return builder.fdiv(left, right)
            return builder.sdiv(left, right)
        elif infix_op == TokenType.STAR:
            return builder.mul(left, right)
        raise CodeGenError(f"Unknown infix operator {infix_op}")

class ReturnNode(ASTNode):
    def __init__(self, token: Token):
        super().__init__(token)

    def codegen(self, builder, module, symbol_table):
        if not self.children:
            builder.ret_void()
            return
        value_node = self.children[0]
        value = value_node.codegen(builder, module, symbol_table)
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
            raise CodeGenError("Function is not implemented yet")
        else: # infix operations and IDENTIFIER token
            var_addr = builder.alloca(value.type, name=identifier_node.token.value)
            builder.store(value, var_addr)

        symbol_table[identifier_node.token.value] = var_addr
        return var_addr
