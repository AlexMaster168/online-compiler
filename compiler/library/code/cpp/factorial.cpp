// Факториал рекурсией. constexpr — компилятор может посчитать его ещё при сборке.
#include <cstdint>
#include <iostream>

constexpr std::uint64_t factorial(int n) { return n <= 1 ? 1 : n * factorial(n - 1); }

int main() {
    std::cout << "10! = " << factorial(10) << '\n';
    std::cout << "20! = " << factorial(20) << '\n';
}
