// Бинарный поиск: O(log n). Int? вместо магического -1.
func binarySearch(_ a: [Int], _ target: Int) -> Int? {
    var lo = 0, hi = a.count - 1
    while lo <= hi {
        let mid = lo + (hi - lo) / 2
        if a[mid] == target { return mid }
        if a[mid] < target { lo = mid + 1 } else { hi = mid - 1 }
    }
    return nil
}

let arr = [1, 3, 5, 7, 9, 11, 13, 15, 17, 19]
for target in [7, 4] {
    if let i = binarySearch(arr, target) {
        print("Found \(target) at index \(i)")
    } else {
        print("\(target) not found")
    }
}
