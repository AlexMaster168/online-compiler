# НОД по Евклиду. (В Julia есть встроенные gcd/lcm — пишем свои с другими именами.)
my_gcd(a, b) = b == 0 ? a : my_gcd(b, a % b)
my_lcm(a, b) = a ÷ my_gcd(a, b) * b

println("GCD(48, 18) = ", my_gcd(48, 18))
println("LCM(48, 18) = ", my_lcm(48, 18))
