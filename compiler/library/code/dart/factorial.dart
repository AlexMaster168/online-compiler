// Факториал рекурсией. int в Dart VM — 64 бита, 20! помещается.
int factorial(int n) => n <= 1 ? 1 : n * factorial(n - 1);

void main() {
  print('10! = ${factorial(10)}');
  print('20! = ${factorial(20)}');
}
