// Быстрое возведение в степень: O(log n).
const mod = 1000000007;

int powerMod(int base, int exp, int m) {
  var result = 1;
  base %= m;
  while (exp > 0) {
    if (exp & 1 == 1) result = result * base % m;
    base = base * base % m;
    exp >>= 1;
  }
  return result;
}

void main() {
  print('2^30 mod $mod = ${powerMod(2, 30, mod)}');
  print('3^200 mod $mod = ${powerMod(3, 200, mod)}');
}
