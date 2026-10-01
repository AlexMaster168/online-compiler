// Ханойские башни: 2^n - 1 ходов.
#include <iostream>

int moves = 0;

void hanoi(int n, char source, char spare, char target) {
    if (n == 0) return;
    hanoi(n - 1, source, target, spare);
    std::cout << "Move disk " << n << " from " << source << " to " << target << '\n';
    ++moves;
    hanoi(n - 1, spare, source, target);
}

int main() {
    hanoi(3, 'A', 'B', 'C');
    std::cout << "Total moves: " << moves << '\n';
}
