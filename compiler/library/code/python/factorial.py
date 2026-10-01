# Факториал рекурсией: n! = n * (n - 1)!, база 0! = 1.


def factorial(n):
    return 1 if n <= 1 else n * factorial(n - 1)


print(f"10! = {factorial(10)}")
print(f"20! = {factorial(20)}")
