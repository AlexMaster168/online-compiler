// Бинарный поиск: O(log n). В STL есть std::lower_bound — здесь пишем руками.
#include <iostream>
#include <vector>

int binarySearch(const std::vector<int>& a, int target) {
    int lo = 0, hi = static_cast<int>(a.size()) - 1;
    while (lo <= hi) {
        int mid = lo + (hi - lo) / 2;
        if (a[mid] == target) return mid;
        if (a[mid] < target) lo = mid + 1;
        else hi = mid - 1;
    }
    return -1;
}

int main() {
    const std::vector<int> a{1, 3, 5, 7, 9, 11, 13, 15, 17, 19};
    for (int target : {7, 4}) {
        int i = binarySearch(a, target);
        if (i >= 0) std::cout << "Found " << target << " at index " << i << '\n';
        else std::cout << target << " not found\n";
    }
}
