// Числа Фибоначчи генератором sync*: значения выдаются лениво через yield.
Iterable<int> fibonacci() sync* {
  var (a, b) = (0, 1);
  while (true) {
    yield a;
    (a, b) = (b, a + b);
  }
}

void main() {
  print('Fibonacci: ${fibonacci().take(15).join(' ')}');
  print('F(50) = ${fibonacci().elementAt(50)}');
}
