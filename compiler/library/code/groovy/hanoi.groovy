// Ханойские башни: 2^n - 1 ходов. Метод возвращает число ходов.
int hanoi(int n, String source, String spare, String target) {
    if (n == 0) return 0
    int before = hanoi(n - 1, source, target, spare)
    println "Move disk $n from $source to $target"
    before + 1 + hanoi(n - 1, spare, source, target)
}

println "Total moves: ${hanoi(3, 'A', 'B', 'C')}"
