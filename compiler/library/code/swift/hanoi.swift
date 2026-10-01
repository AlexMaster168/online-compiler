// Ханойские башни: 2^n - 1 ходов. @discardableResult — можно вызывать, не используя результат.
@discardableResult
func hanoi(_ n: Int, _ source: String, _ spare: String, _ target: String) -> Int {
    guard n > 0 else { return 0 }
    let before = hanoi(n - 1, source, target, spare)
    print("Move disk \(n) from \(source) to \(target)")
    return before + 1 + hanoi(n - 1, spare, source, target)
}

print("Total moves: \(hanoi(3, "A", "B", "C"))")
