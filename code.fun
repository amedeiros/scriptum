# let strcat = -> (left, right) {
#   let left_len = strlen(left)
#   let right_len = strlen(right)
#   let total_len = left_len + right_len + 1
#   let result = malloc(total_len)
#   strcpy(result, left)
#   strcpy(result + left_len, right)
#   return result
# }

# Test some basics
let one = 1
let floating = 10.019
let two_hundred = 200
printf("Total: %.2f\n", one + floating)
printf("Total Again!: %d\n", (one * two_hundred) + ((one * 100) / 2))

# Test concat
let x = "apples"
let concat = "Concat: " + x
printf("(%s) and x is now (%s)\n", concat, x)


# Test if statements
let truth = true
if (truth) {
  puts("TRUE!!!")
} else {
  puts("FALSE!!!")
}

if ((truth and 2 == 1.0) or 1 != 1) {
  puts("Yay")
} else {
  # This should run!
  puts("Not yay!")
}

if (x == "apples") {
  puts("I AM APPLE!")
} else {
  puts(x)
  printf("%s NOPE NOT APPLE! \n", x)
}

# Some math
printf("%.2f\n", 10 * 100.0)
printf("%.2f\n", 10 - 1.01)
printf("%.2f\n", 10 + 1.01)
printf("%d\n", 10 + 100)
printf("%d\n", 100 / 10)
printf("%.2f\n", 100 / 10.0)

# Function tests
let add = -> (x: int, y: int): int {
  return x + y
}
printf("Results of Add: %d\n", add(10, 10))

let no_return = -> (x: int, y: int) {
  printf("NO RETURN X: %d Y: %d\n", x, y)
}
no_return(10, 20)

let emprty_return = -> () {
  puts("EMPTY RETURN")
  return
}
emprty_return()

# Print a string from a function
let print_msg = -> (msg: str) {
  printf("Message: %s\n", msg)
}
print_msg("Hello from Scriptum!")

# Verify scoping and reassignment
let expected = x
if (expected == x) {
  printf("Expected (%s) == x (%s) are equal!\n", expected, x)
} else {
  printf("Expected (%s) == x (%s) are NOT equal!\n", expected, x)
}

let scoping_test = -> () {
  let x = 10
  printf("Inside the scope! X: %d\n", x)
}
scoping_test()
printf("Outside the scope! X: %s\n", x)

# Functions as params
let call = -> (func: callable[int, int]:int, x: int, y: int): int {
    return func(x, y)
}
printf("Nested: %d\n", call(add, 2, 3))


let test_func_call = -> (func: callable[int, int]:int, x: int, y: int) {
  let left = func(x, y)
  printf("Left Expect 50: %d\n", left)
  let right = func(func(x, y), func(x, y))
  printf("Right Expect 100: %d\n", right)
  let results = left + right
  printf("Results Expect 150: %d\n", results)
}
test_func_call(add, 20, 30)

# Recursive functions
let fact = -> (x: int): int {
  if (x <= 1) {
    return 1
  }
  
  return x * fact(x - 1)
}
printf("Factorial 5: %d\n", fact(5))
printf("Factorial 10: %d\n", fact(10))

# While loops
let n = 10
while (n > 0) {
  printf("N is now: %d\n", n)
  n = n - 1
}

# Data structures
let arr = [1, 2, 3, 4, 5]
printf("Array size: %d\n", alen(arr))
printf("Array Index 0 should be 1: %d\n", arr[0])

let pp_int_array = -> (arr: array[int]) {
  let size_a = alen(arr)
  let end_list = size_a - 1
  let n = 0
  printf("Array Contents: [")
  while (n < size_a) {
    let array_value = arr[n]
    if (n == end_list) {
      printf("%d", array_value)
    } else {
      printf("%d,", array_value)
    }
    n = n + 1
  }
  printf("]\n")
}
pp_int_array(arr)

# Test array assignment
arr[2] = 100
printf("Array Index 2 after assignment should be 100: %d\n", arr[2])

# Array litteral tests
printf("Array Litteral Insdex 1 value should be 3.14: %.2f\n", [1.4, 3.14, 5.687][1])
printf("Array Litteral Index 1 value should be 3: %d\n", [1, 3, 5][1])
printf("Array Litteral Index 2 value should be true (1): %d\n", [true, false, true][2])
printf("Array Litteral Index 0 value should be 'scriptum': %s\n", ["hello", "world", "from", "scriptum"][3])

let float_arr = [1.1, 2.2, 3.3, 4.4]
printf("Float array size should be 4: %d\n", alen(float_arr))
let string_arr = ["one", "two", "three"]
printf("String array size should be 3: %d\n", alen(string_arr))
let bool_arr = [true, false]
printf("Bool array size should be 2: %d\n", alen(bool_arr))
let int_arr = [10, 20, 30, 40, 50]
printf("Int array size should be 5: %d\n", alen(int_arr))

append(float_arr, 5.5)
printf("Float array size after append should be 5: %d with value 5.5: %.2f\n", alen(float_arr), float_arr[4])
append(string_arr, "four")
printf("String array size after append should be 4: %d with value 'four': %s\n", alen(string_arr), string_arr[3])
append(bool_arr, true)
printf("Bool array size after append should be 3: %d with value true (1): %d\n", alen(bool_arr), bool_arr[2])
append(int_arr, 60)
printf("Int array size after append should be 6: %d with value 60: %d\n", alen(int_arr), int_arr[5])

# Array of arrays test
let arr_of_arr = [[1,2,3], [4,5,6], [7,8,9]]
printf("Array of Arrays size should be 3: %d\n", alen(arr_of_arr))
printf("Array of Arrays first element size should be 3: %d\n", alen(arr_of_arr[0]))
printf("Array of Arrays second array second element should be 4: %d\n", arr_of_arr[1][0])
append(arr_of_arr, [10,11,12])
printf("Array of Arrays size after append should be 4: %d\n", alen(arr_of_arr))
printf("Array of Arrays new fourth array third element should be 12: %d\n", arr_of_arr[3][2])
arr_of_arr[0][0] = 100
printf("Array of Arrays first array first element after assignment should be 100: %d\n", arr_of_arr[0][0])

# Test remove
printf("Removed element at index 2 should be 30: %d\n", remove(int_arr, 2))
printf("Removed element at index 0 should be 1.1: %.2f\n", remove(float_arr, 0))
printf("Removed element at index 1 should be 'two': %s\n", remove(string_arr, 1))
printf("Removed element at index 0 should be true (1): %d\n", remove(bool_arr, 0))

# Test pop
printf("Pop element should be 60: %d\n", pop(int_arr))
printf("Pop element should be 5.5: %.2f\n", pop(float_arr))
printf("Pop element should be 'four': %s\n", pop(string_arr))
printf("Pop element should be true (1): %d\n", pop(bool_arr))

# Test Insert
insert(int_arr, 1, 15)
printf("After insert at index 1, element should be 15: %d\n", int_arr[1])
insert(float_arr, 0, 0.5)
printf("After insert at index 0, element should be 0.5: %.2f\n", float_arr[0])
insert(string_arr, 2, "two_point_five")
printf("After insert at index 2, element should be 'two_point_five': %s\n", string_arr[2])
insert(bool_arr, 1, true)
printf("After insert at index 1, element should be true (1): %d\n", bool_arr[1])
insert(arr_of_arr, 2, [20,21,22])
printf("After insert at index 2, array size should be 5: %d\n", alen(arr_of_arr))
printf("Newly inserted array at index 2, second element should be 21: %d\n", arr_of_arr[2][1])

# Test Index Of
printf("Index of 20 in int_arr should be 2: %d\n", index_of(int_arr, 20))
printf("Index of 2.2 in float_arr should be 1: %d\n", index_of(float_arr, 2.2))
printf("Index of 'three' in string_arr should be 1: %d\n", index_of(string_arr, "three"))
printf("Index of true (1) in bool_arr should be 1: %d\n", index_of(bool_arr, true))
printf("Index of [4, 5, 6] in arr_of_arr should be 1: %d\n", index_of(arr_of_arr, [4, 5, 6]))

# Test reverse
reverse(int_arr)
printf("After reverse, int_arr first element should be 50: %d\n", int_arr[0])
reverse(float_arr)
printf("After reverse, float_arr first element should be 4.4: %.2f\n", float_arr[0])
reverse(string_arr)
printf("After reverse, string_arr first element should be 'two_point_five': %s\n", string_arr[0])
reverse(bool_arr)
printf("After reverse, bool_arr first element should be true (1): %d\n", bool_arr[0])
reverse(arr_of_arr)
printf("After reverse, arr_of_arr first element first element should be 10: %d\n", arr_of_arr[0][0])

# Test sort
sort(int_arr)
printf("After sort, int_arr first element should be 10: %d\n", int_arr[0])
sort(float_arr)
printf("After sort, float_arr first element should be 0.5: %.2f\n", float_arr[0])
sort(string_arr)
printf("After sort, string_arr first element should be 'one': %s\n", string_arr[0])
sort(bool_arr)
printf("After sort, bool_arr first element should be false (0): %d\n", bool_arr[0])

# Test clear
clear(int_arr)
printf("After clear, int_arr size should be 0: %d\n", alen(int_arr))
clear(float_arr)
printf("After clear, float_arr size should be 0: %d\n", alen(float_arr))
clear(string_arr)
printf("After clear, string_arr size should be 0: %d\n", alen(string_arr))
clear(bool_arr)
printf("After clear, bool_arr size should be 0: %d\n", alen(bool_arr))
clear(arr_of_arr)
printf("After clear, arr_of_arr size should be 0: %d\n", alen(arr_of_arr))

# Test array replication
let replicated_int_arr = [10] * 5
printf("Replicated int array size should be 5: %d\n", alen(replicated_int_arr))
printf("Replicated int array index 0 should be 10: %d\n", replicated_int_arr[0])

let replicated_value = 1.0
let replicated_count = 4
let replicated_float_arr = [replicated_value] * replicated_count
printf("Replicated float array size should be 4: %d\n", alen(replicated_float_arr))
printf("Replicated float array index 2 should be 1.0: %.2f\n", replicated_float_arr[2])

let replicated_str_arr = ["scriptum"] * 3
printf("Replicated string array size should be 3: %d\n", alen(replicated_str_arr))
printf("Replicated string array index 1 should be 'scriptum': %s\n", replicated_str_arr[1])

let replicated_bool_arr = [false] * 6
printf("Replicated bool array size should be 6: %d\n", alen(replicated_bool_arr))
printf("Replicated bool array index 4 should be false (0): %d\n", replicated_bool_arr[4])

let replicated_arr_of_arr = [[0]] * 2
printf("Replicated array of arrays size should be 2: %d\n", alen(replicated_arr_of_arr))
printf("Replicated array of arrays index 1 index 0 should be 0: %d\n", replicated_arr_of_arr[1][0])
