// Быстрое возведение в степень: O(log n).
#include <cstdint>
#include <iostream>

constexpr std::int64_t MOD = 1'000'000'007;

std::int64_t powerMod(std::int64_t base, std::int64_t exp, std::int64_t mod) {
    std::int64_t result = 1;
    base %= mod;
    while (exp > 0) {
        if (exp & 1) result = result * base % mod;
        base = base * base % mod;
        exp >>= 1;
    }
    return result;
}

int main() {
    std::cout << "2^30 mod " << MOD << " = " << powerMod(2, 30, MOD) << '\n';
    std::cout << "3^200 mod " << MOD << " = " << powerMod(3, 200, MOD) << '\n';
}
