// Сортировка слиянием: всегда O(n log n), стабильная.
func mergeSort(_ a: [Int]) -> [Int] {
    guard a.count > 1 else { return a }
    let left = mergeSort(Array(a[..<(a.count / 2)]))
    let right = mergeSort(Array(a[(a.count / 2)...]))
    var merged: [Int] = []
    merged.reserveCapacity(a.count)
    var i = 0, j = 0
    while i < left.count && j < right.count {
        if left[i] <= right[j] {
            merged.append(left[i]); i += 1
        } else {
            merged.append(right[j]); j += 1
        }
    }
    return merged + left[i...] + right[j...]
}

print("Sorted:", mergeSort([38, 27, 43, 3, 9, 82, 10]).map(String.init).joined(separator: " "))
