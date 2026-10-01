// Факториал рекурсией. BigInteger (суффикс G у литерала) — длинная арифметика.
BigInteger factorial(int n) { n <= 1 ? 1G : n * factorial(n - 1) }

println "10! = ${factorial(10)}"
println "20! = ${factorial(20)}"
