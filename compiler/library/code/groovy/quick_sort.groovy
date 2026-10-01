// Быстрая сортировка: опора — первый элемент, split делит остальные по условию.
def quickSort(List<Integer> list) {
    if (list.size() <= 1) return list
    def pivot = list.head()
    def (smaller, larger) = list.tail().split { it < pivot }
    quickSort(smaller) + [pivot] + quickSort(larger)
}

println "Sorted: ${quickSort([10, 7, 8, 9, 1, 5, 3]).join(' ')}"
