// Сортировка пузырьком: O(n^2). Если за проход не было обменов — массив уже отсортирован.
func bubbleSort(_ input: [Int]) -> [Int] {
    var a = input
    for i in 0..<max(a.count - 1, 0) {
        var swapped = false
        for j in 0..<(a.count - 1 - i) where a[j] > a[j + 1] {
            a.swapAt(j, j + 1)
            swapped = true
        }
        if !swapped { break }
    }
    return a
}

print("Sorted:", bubbleSort([5, 2, 9, 1, 5, 6]).map(String.init).joined(separator: " "))
