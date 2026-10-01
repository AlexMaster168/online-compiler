// Быстрая сортировка (разбиение Ломуто): в среднем O(n log n), в худшем O(n^2).
fun IntArray.swap(i: Int, j: Int) {
    this[i] = this[j].also { this[j] = this[i] }
}

fun partition(a: IntArray, lo: Int, hi: Int): Int {
    val pivot = a[hi]
    var i = lo
    for (j in lo until hi) {
        if (a[j] < pivot) a.swap(i++, j)
    }
    a.swap(i, hi)
    return i
}

fun quickSort(a: IntArray, lo: Int = 0, hi: Int = a.size - 1) {
    if (lo >= hi) return
    val p = partition(a, lo, hi)
    quickSort(a, lo, p - 1)
    quickSort(a, p + 1, hi)
}

fun main() {
    val a = intArrayOf(10, 7, 8, 9, 1, 5, 3)
    quickSort(a)
    println("Sorted: " + a.joinToString(" "))
}
