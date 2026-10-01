# Быстрое возведение в степень: O(log n) умножений. В Python есть встроенный pow(a, n, m) — пишем руками.
MOD = 1_000_000_007


def power_mod(base, exp, mod):
    result = 1
    base %= mod
    while exp > 0:
        if exp & 1:
            result = result * base % mod
        base = base * base % mod
        exp >>= 1
    return result


print(f"2^30 mod {MOD} = {power_mod(2, 30, MOD)}")
print(f"3^200 mod {MOD} = {power_mod(3, 200, MOD)}")
