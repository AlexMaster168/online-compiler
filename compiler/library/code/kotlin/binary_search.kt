// Бинарный поиск: O(log n). (В стандартной библиотеке есть List.binarySearch — пишем руками.)
fun binarySearch(a: IntArray, target: Int): Int {
    var lo = 0
    var hi = a.size - 1
    while (lo <= hi) {
        val mid = (lo + hi) ushr 1
        when {
            a[mid] == target -> return mid
            a[mid] < target -> lo = mid + 1
            else -> hi = mid - 1
        }
    }
    return -1
}

fun main() {
    val a = intArrayOf(1, 3, 5, 7, 9, 11, 13, 15, 17, 19)
    for (target in listOf(7, 4)) {
        val i = binarySearch(a, target)
        println(if (i >= 0) "Found $target at index $i" else "$target not found")
    }
}
