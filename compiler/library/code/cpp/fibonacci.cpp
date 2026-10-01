// Числа Фибоначчи итеративно, O(n).
#include <cstdint>
#include <iostream>

std::uint64_t fib(int n) {
    std::uint64_t a = 0, b = 1;
    for (int i = 0; i < n; ++i) {
        std::uint64_t t = a + b;
        a = b;
        b = t;
    }
    return a;
}

int main() {
    std::cout << "Fibonacci:";
    for (int i = 0; i < 15; ++i) std::cout << ' ' << fib(i);
    std::cout << "\nF(50) = " << fib(50) << '\n';
}
