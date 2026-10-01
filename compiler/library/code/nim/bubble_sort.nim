# Сортировка пузырьком: var-параметр меняется на месте.
import std/strutils

proc bubbleSort(a: var seq[int]) =
  for i in 0 ..< a.len - 1:
    var swapped = false
    for j in 0 ..< a.len - 1 - i:
      if a[j] > a[j + 1]:
        swap(a[j], a[j + 1])
        swapped = true
    if not swapped: break

var a = @[5, 2, 9, 1, 5, 6]
bubbleSort(a)
echo "Sorted: ", a.join(" ")
