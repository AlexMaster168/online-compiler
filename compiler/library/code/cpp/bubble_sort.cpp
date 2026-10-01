// Сортировка пузырьком: O(n^2). Если за проход не было обменов — массив уже отсортирован.
#include <iostream>
#include <utility>
#include <vector>

void bubbleSort(std::vector<int>& a) {
    for (std::size_t i = 0; i + 1 < a.size(); ++i) {
        bool swapped = false;
        for (std::size_t j = 0; j + 1 < a.size() - i; ++j) {
            if (a[j] > a[j + 1]) {
                std::swap(a[j], a[j + 1]);
                swapped = true;
            }
        }
        if (!swapped) break;
    }
}

int main() {
    std::vector<int> a{5, 2, 9, 1, 5, 6};
    bubbleSort(a);
    std::cout << "Sorted:";
    for (int x : a) std::cout << ' ' << x;
    std::cout << '\n';
}
