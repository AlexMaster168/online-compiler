# Сортировка слиянием: всегда O(n log n), стабильная, нужна O(n) доп. памяти.


def merge_sort(a):
    if len(a) <= 1:
        return a
    mid = len(a) // 2
    left, right = merge_sort(a[:mid]), merge_sort(a[mid:])
    merged, i, j = [], 0, 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            merged.append(left[i])
            i += 1
        else:
            merged.append(right[j])
            j += 1
    return merged + left[i:] + right[j:]


print("Sorted:", *merge_sort([38, 27, 43, 3, 9, 82, 10]))
