// Ханойские башни: 2^n - 1 ходов. Функция возвращает число сделанных ходов.
fun hanoi(n: Int, source: Char, spare: Char, target: Char): Int {
    if (n == 0) return 0
    val before = hanoi(n - 1, source, target, spare)
    println("Move disk $n from $source to $target")
    return before + 1 + hanoi(n - 1, spare, source, target)
}

fun main() {
    println("Total moves: " + hanoi(3, 'A', 'B', 'C'))
}
