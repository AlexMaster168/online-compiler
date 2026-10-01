// Быстрое возведение в степень: O(log n).
final long MOD = 1_000_000_007L

long powerMod(long base, long exp, long m) {
    long result = 1
    base %= m
    while (exp > 0) {
        if (exp & 1) result = result * base % m
        base = base * base % m
        exp >>= 1
    }
    result
}

println "2^30 mod $MOD = ${powerMod(2, 30, MOD)}"
println "3^200 mod $MOD = ${powerMod(3, 200, MOD)}"
