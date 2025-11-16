foreign alen = -> (a: array): int

foreign aclear = -> (a: array): void

foreign areverse = -> (a: array): void

foreign asort = -> (a: array): void

foreign pp_array = -> (a: array): void

foreign create_int_array = -> (size: int): array

foreign delete_int_array = -> (a: array): void

foreign int_array_get = -> (a: array, index: int): int

foreign int_array_set = -> (a: array, index: int, value: int): void

foreign int_array_push_back = -> (a: array, value: int): void

foreign int_array_remove = -> (a: array, index: int): int

foreign int_array_pop = -> (a: array): int

foreign int_array_insert = -> (a: array, index: int, value: int): void

foreign int_array_index_of = -> (a: array, value: int): int

foreign create_int_array_from_value = -> (value: int, size: int): array

foreign create_float_array = -> (size: int): array

foreign delete_float_array = -> (a: array): void

foreign float_array_get = -> (a: array, index: int): float

foreign float_array_set = -> (a: array, index: int, value: float): void

foreign float_array_push_back = -> (a: array, value: float): void

foreign float_array_remove = -> (a: array, index: int): float

foreign float_array_pop = -> (a: array): float

foreign float_array_insert = -> (a: array, index: int, value: float): void

foreign float_array_index_of = -> (a: array, value: float): int

foreign create_float_array_from_value = -> (value: float, size: int): array

foreign create_bool_array = -> (size: int): array

foreign delete_bool_array = -> (a: array): void

foreign bool_array_get = -> (a: array, index: int): bool

foreign bool_array_set = -> (a: array, index: int, value: bool): void

foreign bool_array_push_back = -> (a: array, value: bool): void

foreign bool_array_remove = -> (a: array, index: int): bool

foreign bool_array_pop = -> (a: array): bool

foreign bool_array_insert = -> (a: array, index: int, value: bool): void

foreign bool_array_index_of = -> (a: array, value: bool): int

foreign create_bool_array_from_value = -> (value: bool, size: int): array

foreign create_string_array = -> (size: int): array

foreign delete_string_array = -> (a: array): void

foreign string_array_get = -> (a: array, index: int): str

foreign string_array_set = -> (a: array, index: int, value: str): void

foreign string_array_push_back = -> (a: array, value: str): void

foreign string_array_remove = -> (a: array, index: int): str

foreign string_array_pop = -> (a: array): str

foreign string_array_insert = -> (a: array, index: int, value: str): void

foreign string_array_index_of = -> (a: array, value: str): int

foreign create_string_array_from_value = -> (value: str, size: int): array

foreign create_array_array = -> (size: int): array

foreign delete_array_array = -> (a: array): void

foreign array_array_get = -> (a: array, index: int): array

foreign array_array_set = -> (a: array, index: int, value: array): void

foreign array_array_push_back = -> (a: array, value: array): void

foreign array_array_remove = -> (a: array, index: int): array

foreign array_array_pop = -> (a: array): array

foreign array_array_insert = -> (a: array, index: int, value: array): void

foreign array_array_index_of = -> (a: array, value: array): int

foreign create_array_array_from_value = -> (value: array, size: int): array
