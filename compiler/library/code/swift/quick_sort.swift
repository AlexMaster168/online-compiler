// Быстрая сортировка (разбиение Ломуто): inout — массив сортируется на месте.
func partition(_ a: inout [Int], _ lo: Int, _ hi: Int) -> Int {
    let pivot = a[hi]
    var i = lo
    for j in lo..<hi where a[j] < pivot {
        a.swapAt(i, j)
        i += 1
    }
    a.swapAt(i, hi)
    return i
}

func quickSort(_ a: inout [Int], _ lo: Int, _ hi: Int) {
    guard lo < hi else { return }
    let p = partition(&a, lo, hi)
    quickSort(&a, lo, p - 1)
    quickSort(&a, p + 1, hi)
}

var data = [10, 7, 8, 9, 1, 5, 3]
quickSort(&data, 0, data.count - 1)
print("Sorted:", data.map(String.init).joined(separator: " "))
