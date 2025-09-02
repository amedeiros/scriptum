let x = "apples"
let one = 1
let two_hundred = 200
let floating = 10.019
let truth = true
let falsity = false
let apples = floating
let concat = "Concat: " + x 
# return apples
# return
if (truth) {
  puts("TRUE!!!")
  puts(concat)
  printf("Total: %.2f\n", one + floating)
  printf("Total Again!: %d\n", (one * two_hundred) + ((one * 100) / 2))
} else {
  puts("FALSE!!!")
}

if ((truth and 2 == 1.0) or 1 != 1) {
  puts("Yay")
} else {
  # This should run!
  puts("Not yay!")
}

if ("apples" == "apples") {
  puts("I AM APPLE!")
} else {
  puts("NOPE NOT APPLE!")
}

printf("%.2f\n", 10 * 100.0)
printf("%.2f\n", 10 - 1.01)
printf("%.2f\n", 10 + 1.01)
printf("%d\n", 10 + 100)
printf("%d\n", 100 / 10)
printf("%.2f\n", 100 / 10.0)
