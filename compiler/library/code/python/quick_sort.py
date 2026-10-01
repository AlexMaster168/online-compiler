# Быстрая сортировка (разбиение Ломуто): в среднем O(n log n), в худшем O(n^2).


def partition(a, lo, hi):
    pivot = a[hi]
    i = lo
    for j in range(lo, hi):
        if a[j] < pivot:
            a[i], a[j] = a[j], a[i]
            i += 1
    a[i], a[hi] = a[hi], a[i]
    return i


def quick_sort(a, lo=0, hi=None):
    if hi is None:
        hi = len(a) - 1
    if lo < hi:
        p = partition(a, lo, hi)
        quick_sort(a, lo, p - 1)
        quick_sort(a, p + 1, hi)


data = [10, 7, 8, 9, 1, 5, 3]
quick_sort(data)
print("Sorted:", *data)
