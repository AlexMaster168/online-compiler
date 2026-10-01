// Сортировка слиянием: срезы списка list[0..<mid] через диапазоны.
def mergeSort(List<Integer> list) {
    if (list.size() <= 1) return list
    int mid = list.size().intdiv(2)
    def left = mergeSort(list[0..<mid])
    def right = mergeSort(list[mid..<list.size()])
    def merged = []
    int i = 0, j = 0
    while (i < left.size() && j < right.size()) {
        merged << (left[i] <= right[j] ? left[i++] : right[j++])
    }
    merged + left.drop(i) + right.drop(j)
}

println "Sorted: ${mergeSort([38, 27, 43, 3, 9, 82, 10]).join(' ')}"
