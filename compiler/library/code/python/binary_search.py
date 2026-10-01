# Бинарный поиск: O(log n), массив обязан быть отсортирован.


def binary_search(a, target):
    lo, hi = 0, len(a) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if a[mid] == target:
            return mid
        if a[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1


arr = [1, 3, 5, 7, 9, 11, 13, 15, 17, 19]
for target in (7, 4):
    i = binary_search(arr, target)
    print(f"Found {target} at index {i}" if i >= 0 else f"{target} not found")
