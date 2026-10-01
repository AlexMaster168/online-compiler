# Сортировка пузырьком: O(n^2). Если за проход не было обменов — массив уже отсортирован.


def bubble_sort(a):
    a = list(a)
    n = len(a)
    for i in range(n - 1):
        swapped = False
        for j in range(n - 1 - i):
            if a[j] > a[j + 1]:
                a[j], a[j + 1] = a[j + 1], a[j]
                swapped = True
        if not swapped:
            break
    return a


print("Sorted:", *bubble_sort([5, 2, 9, 1, 5, 6]))
