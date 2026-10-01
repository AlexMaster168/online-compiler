// Быстрое возведение в степень: O(log n). Произведение по модулю 1e9+7 — через bigint.
const MOD = 1000000007n;

function powerMod(base: bigint, exp: bigint, mod: bigint): bigint {
  let result = 1n;
  base %= mod;
  while (exp > 0n) {
    if (exp & 1n) result = (result * base) % mod;
    base = (base * base) % mod;
    exp >>= 1n;
  }
  return result;
}

console.log(`2^30 mod ${MOD} = ${powerMod(2n, 30n, MOD)}`);
console.log(`3^200 mod ${MOD} = ${powerMod(3n, 200n, MOD)}`);
