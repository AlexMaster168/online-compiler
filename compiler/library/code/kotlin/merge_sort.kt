// Сортировка слиянием: всегда O(n log n), стабильная.
fun mergeSort(a: List<Int>): List<Int> {
    if (a.size <= 1) return a
    val left = mergeSort(a.subList(0, a.size / 2))
    val right = mergeSort(a.subList(a.size / 2, a.size))
    val merged = ArrayList<Int>(a.size)
    var i = 0
    var j = 0
    while (i < left.size && j < right.size) {
        merged += if (left[i] <= right[j]) left[i++] else right[j++]
    }
    merged += left.subList(i, left.size)
    merged += right.subList(j, right.size)
    return merged
}

fun main() {
    println("Sorted: " + mergeSort(listOf(38, 27, 43, 3, 9, 82, 10)).joinToString(" "))
}
