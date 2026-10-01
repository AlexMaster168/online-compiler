// Факториал рекурсией. 20! — предел Int (64 бита); переполнение в Swift — ошибка времени выполнения.
func factorial(_ n: Int) -> Int { n <= 1 ? 1 : n * factorial(n - 1) }

print("10! = \(factorial(10))")
print("20! = \(factorial(20))")
