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
let add = -> (x, y) {
  printf("X: %d\n", x)
  printf("Y: %d\n", y)
  return x + y
}
printf("Results of Add: %d\n", add(10, 10))

let no_return = -> (x, y) {
  printf("NO RETURN X: %d Y: %d\n", x, y)
}
no_return(10, 20)

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
let call = -> (func, x, y) {
    return func(x, y)
}
printf("%d\n", call(add, 2, 3))


let test_func_call = -> (func, x, y) {
  let results = func(x, y) + 1
  printf("Results Expect 51: %d\n", results)
}
test_func_call(add, 20, 30)