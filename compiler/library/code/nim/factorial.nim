# Факториал рекурсией. int в Nim — 64 бита на 64-битной платформе, 20! помещается.
proc factorial(n: int): int =
  if n <= 1: 1 else: n * factorial(n - 1)

echo "10! = ", factorial(10)
echo "20! = ", factorial(20)
