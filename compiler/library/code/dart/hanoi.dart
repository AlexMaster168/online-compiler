// Ханойские башни: 2^n - 1 ходов. Возвращаем число ходов.
int hanoi(int n, String source, String spare, String target) {
  if (n == 0) return 0;
  final before = hanoi(n - 1, source, target, spare);
  print('Move disk $n from $source to $target');
  return before + 1 + hanoi(n - 1, spare, source, target);
}

void main() {
  print('Total moves: ${hanoi(3, 'A', 'B', 'C')}');
}
