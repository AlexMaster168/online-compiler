# Ханойские башни: 2^n - 1 ходов. Процедура возвращает число ходов.
proc hanoi(n: int, source, spare, target: char): int =
  if n == 0: return 0
  let before = hanoi(n - 1, source, target, spare)
  echo "Move disk ", n, " from ", source, " to ", target
  before + 1 + hanoi(n - 1, spare, source, target)

echo "Total moves: ", hanoi(3, 'A', 'B', 'C')
