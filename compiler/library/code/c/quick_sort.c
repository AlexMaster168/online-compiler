// Быстрая сортировка (разбиение Ломуто): в среднем O(n log n), в худшем O(n^2).
#include <stdio.h>

static void swap(int *x, int *y) {
    int t = *x;
    *x = *y;
    *y = t;
}

static int partition(int *a, int lo, int hi) {
    int pivot = a[hi], i = lo;
    for (int j = lo; j < hi; j++)
        if (a[j] < pivot) swap(&a[i++], &a[j]);
    swap(&a[i], &a[hi]);
    return i;
}

void quick_sort(int *a, int lo, int hi) {
    if (lo >= hi) return;
    int p = partition(a, lo, hi);
    quick_sort(a, lo, p - 1);
    quick_sort(a, p + 1, hi);
}

int main(void) {
    int a[] = {10, 7, 8, 9, 1, 5, 3};
    int n = sizeof a / sizeof a[0];
    quick_sort(a, 0, n - 1);
    printf("Sorted:");
    for (int i = 0; i < n; i++) printf(" %d", a[i]);
    printf("\n");
    return 0;
}
