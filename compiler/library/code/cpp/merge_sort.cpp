// Сортировка слиянием: всегда O(n log n), стабильная.
#include <iostream>
#include <vector>

std::vector<int> mergeSort(const std::vector<int>& a) {
    if (a.size() <= 1) return a;
    auto mid = a.begin() + a.size() / 2;
    auto left = mergeSort({a.begin(), mid});
    auto right = mergeSort({mid, a.end()});
    std::vector<int> merged;
    merged.reserve(a.size());
    std::size_t i = 0, j = 0;
    while (i < left.size() && j < right.size())
        merged.push_back(left[i] <= right[j] ? left[i++] : right[j++]);
    merged.insert(merged.end(), left.begin() + i, left.end());
    merged.insert(merged.end(), right.begin() + j, right.end());
    return merged;
}

int main() {
    std::cout << "Sorted:";
    for (int x : mergeSort({38, 27, 43, 3, 9, 82, 10})) std::cout << ' ' << x;
    std::cout << '\n';
}
