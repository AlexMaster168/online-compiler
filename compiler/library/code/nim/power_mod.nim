# Быстрое возведение в степень: O(log n).
const Mod = 1_000_000_007

proc powerMod(base, exp, m: int): int =
  result = 1
  var b = base mod m
  var e = exp
  while e > 0:
    if (e and 1) == 1: result = result * b mod m
    b = b * b mod m
    e = e shr 1

echo "2^30 mod ", Mod, " = ", powerMod(2, 30, Mod)
echo "3^200 mod ", Mod, " = ", powerMod(3, 200, Mod)
