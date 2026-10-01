// НОД по Евклиду. В C++17 есть std::gcd / std::lcm из <numeric> — здесь пишем руками.
#include <iostream>

long long gcd(long long a, long long b) { return b == 0 ? a : gcd(b, a % b); }
long long lcm(long long a, long long b) { return a / gcd(a, b) * b; }

int main() {
    std::cout << "GCD(48, 18) = " << gcd(48, 18) << '\n';
    std::cout << "LCM(48, 18) = " << lcm(48, 18) << '\n';
}
