// Быстрая сортировка (разбиение Ломуто): в среднем O(n log n), в худшем O(n^2).
#include <iostream>
#include <utility>
#include <vector>

int partition(std::vector<int>& a, int lo, int hi) {
    int pivot = a[hi], i = lo;
    for (int j = lo; j < hi; ++j)
        if (a[j] < pivot) std::swap(a[i++], a[j]);
    std::swap(a[i], a[hi]);
    return i;
}

void quickSort(std::vector<int>& a, int lo, int hi) {
    if (lo >= hi) return;
    int p = partition(a, lo, hi);
    quickSort(a, lo, p - 1);
    quickSort(a, p + 1, hi);
}

int main() {
    std::vector<int> a{10, 7, 8, 9, 1, 5, 3};
    quickSort(a, 0, static_cast<int>(a.size()) - 1);
    std::cout << "Sorted:";
    for (int x : a) std::cout << ' ' << x;
    std::cout << '\n';
}
