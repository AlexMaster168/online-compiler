# Числа Фибоначчи итеративно. Int в Julia — 64 бита, F(50) помещается.
function fib(n)
    a, b = 0, 1
    for _ in 1:n
        a, b = b, a + b
    end
    a
end

println("Fibonacci: ", join(fib.(0:14), " "))  # fib.( ) — применить функцию к каждому элементу
println("F(50) = ", fib(50))
