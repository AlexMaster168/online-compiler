# Числа Фибоначчи итератором: iterator + yield отдают значения по одному.
import std/[enumerate, strutils]

iterator fibonacci(count: int): int64 =
  var (a, b) = (0'i64, 1'i64)
  for _ in 0 ..< count:
    yield a
    (a, b) = (b, a + b)

var first: seq[int64]
var last: int64
for i, f in enumerate(fibonacci(51)):
  if i < 15: first.add f
  last = f
echo "Fibonacci: ", first.join(" ")
echo "F(50) = ", last
