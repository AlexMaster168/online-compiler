// Решето Эратосфена: O(n log log n). vector<bool> хранит по биту на число.
#include <iostream>
#include <vector>

std::vector<int> sieve(int n) {
    std::vector<bool> isPrime(n + 1, true);
    std::vector<int> primes;
    for (int p = 2; p <= n; ++p) {
        if (!isPrime[p]) continue;
        primes.push_back(p);
        for (long long k = 1LL * p * p; k <= n; k += p) isPrime[k] = false;
    }
    return primes;
}

int main() {
    std::cout << "Primes up to 50:";
    for (int p : sieve(50)) std::cout << ' ' << p;
    std::cout << '\n';
}
