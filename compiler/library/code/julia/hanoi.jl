# Ханойские башни: 2^n - 1 ходов. Функция возвращает число ходов.
function hanoi(n, source, spare, target)
    n == 0 && return 0
    before = hanoi(n - 1, source, target, spare)
    println("Move disk $n from $source to $target")
    before + 1 + hanoi(n - 1, spare, source, target)
end

println("Total moves: ", hanoi(3, 'A', 'B', 'C'))
