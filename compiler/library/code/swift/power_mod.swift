// Быстрое возведение в степень: O(log n).
let mod = 1_000_000_007

func powerMod(_ base: Int, _ exp: Int, _ m: Int) -> Int {
    var result = 1, b = base % m, e = exp
    while e > 0 {
        if e & 1 == 1 { result = result * b % m }
        b = b * b % m
        e >>= 1
    }
    return result
}

print("2^30 mod \(mod) = \(powerMod(2, 30, mod))")
print("3^200 mod \(mod) = \(powerMod(3, 200, mod))")
