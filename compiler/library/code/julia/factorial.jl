# Факториал рекурсией. Int64 хватает до 20!; для больших n — big(n).
fact(n) = n <= 1 ? 1 : n * fact(n - 1)

println("10! = ", fact(10))
println("20! = ", fact(20))
