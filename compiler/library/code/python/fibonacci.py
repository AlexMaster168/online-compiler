# Числа Фибоначчи итеративно: O(n) времени и O(1) памяти.


def fib(n):
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a


print("Fibonacci:", *(fib(i) for i in range(15)))
print(f"F(50) = {fib(50)}")
