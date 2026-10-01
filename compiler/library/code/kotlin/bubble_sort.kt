// Сортировка пузырьком: O(n^2). Если за проход не было обменов — массив уже отсортирован.
fun bubbleSort(a: IntArray) {
    for (i in 0 until a.size - 1) {
        var swapped = false
        for (j in 0 until a.size - 1 - i) {
            if (a[j] > a[j + 1]) {
                a[j] = a[j + 1].also { a[j + 1] = a[j] }
                swapped = true
            }
        }
        if (!swapped) break
    }
}

fun main() {
    val a = intArrayOf(5, 2, 9, 1, 5, 6)
    bubbleSort(a)
    println("Sorted: " + a.joinToString(" "))
}
