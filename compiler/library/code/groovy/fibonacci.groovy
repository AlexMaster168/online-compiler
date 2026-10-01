// Числа Фибоначчи итеративно; long — 64 бита, F(50) помещается.
long fib(int n) {
    long a = 0, b = 1
    n.times {
        long t = a + b
        a = b
        b = t
    }
    a
}

println "Fibonacci: ${(0..<15).collect { fib(it) }.join(' ')}"
println "F(50) = ${fib(50)}"
