// Бинарный поиск: O(log n). mid = lo + (hi - lo) / 2 — без переполнения на больших индексах.
#include <stdio.h>

int binary_search(const int *a, int n, int target) {
    int lo = 0, hi = n - 1;
    while (lo <= hi) {
        int mid = lo + (hi - lo) / 2;
        if (a[mid] == target) return mid;
        if (a[mid] < target) lo = mid + 1;
        else hi = mid - 1;
    }
    return -1;
}

int main(void) {
    int a[] = {1, 3, 5, 7, 9, 11, 13, 15, 17, 19};
    int targets[] = {7, 4};
    for (int t = 0; t < 2; t++) {
        int i = binary_search(a, 10, targets[t]);
        if (i >= 0) printf("Found %d at index %d\n", targets[t], i);
        else printf("%d not found\n", targets[t]);
    }
    return 0;
}
