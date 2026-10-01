// Сортировка слиянием: всегда O(n log n), стабильная, нужен буфер на n элементов.
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static void merge_sort_rec(int *a, int *tmp, int lo, int hi) {  // [lo, hi)
    if (hi - lo < 2) return;
    int mid = (lo + hi) / 2;
    merge_sort_rec(a, tmp, lo, mid);
    merge_sort_rec(a, tmp, mid, hi);
    int i = lo, j = mid, k = lo;
    while (i < mid && j < hi) tmp[k++] = a[i] <= a[j] ? a[i++] : a[j++];
    while (i < mid) tmp[k++] = a[i++];
    while (j < hi) tmp[k++] = a[j++];
    memcpy(a + lo, tmp + lo, (size_t)(hi - lo) * sizeof *a);
}

void merge_sort(int *a, int n) {
    int *tmp = malloc((size_t)n * sizeof *tmp);
    merge_sort_rec(a, tmp, 0, n);
    free(tmp);
}

int main(void) {
    int a[] = {38, 27, 43, 3, 9, 82, 10};
    int n = sizeof a / sizeof a[0];
    merge_sort(a, n);
    printf("Sorted:");
    for (int i = 0; i < n; i++) printf(" %d", a[i]);
    printf("\n");
    return 0;
}
