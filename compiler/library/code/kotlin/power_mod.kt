// Быстрое возведение в степень: O(log n).
const val MOD = 1_000_000_007L

fun powerMod(base: Long, exp: Long, mod: Long): Long {
    var result = 1L
    var b = base % mod
    var e = exp
    while (e > 0) {
        if (e and 1L == 1L) result = result * b % mod
        b = b * b % mod
        e = e shr 1
    }
    return result
}

fun main() {
    println("2^30 mod $MOD = ${powerMod(2, 30, MOD)}")
    println("3^200 mod $MOD = ${powerMod(3, 200, MOD)}")
}
