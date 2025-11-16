# This file contains compile time FFI functions for I/O operations, such as printing to the console.
# These functions are implemented in C and are available at runtime.

foreign printf = -> (value: str, var_arg: bool = true): int

foreign puts = -> (value: str): int
