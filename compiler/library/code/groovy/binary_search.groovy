// Бинарный поиск: O(log n), массив обязан быть отсортирован.
def binarySearch(List<Integer> a, int target) {
    int lo = 0, hi = a.size() - 1
    while (lo <= hi) {
        int mid = (lo + hi).intdiv(2)  // в Groovy / даёт дробь, intdiv — целое деление
        if (a[mid] == target) return mid
        if (a[mid] < target) lo = mid + 1 else hi = mid - 1
    }
    -1
}

def arr = [1, 3, 5, 7, 9, 11, 13, 15, 17, 19]
[7, 4].each { target ->
    int i = binarySearch(arr, target)
    println(i >= 0 ? "Found $target at index $i" : "$target not found")
}
