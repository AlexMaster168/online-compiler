// Ханойские башни: 2^n - 1 ходов.
#include <stdio.h>

static int moves = 0;

void hanoi(int n, char source, char spare, char target) {
    if (n == 0) return;
    hanoi(n - 1, source, target, spare);
    printf("Move disk %d from %c to %c\n", n, source, target);
    moves++;
    hanoi(n - 1, spare, source, target);
}

int main(void) {
    hanoi(3, 'A', 'B', 'C');
    printf("Total moves: %d\n", moves);
    return 0;
}
