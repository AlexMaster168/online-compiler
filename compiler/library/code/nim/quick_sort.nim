# Быстрая сортировка (разбиение Ломуто) на месте.
import std/strutils

proc quickSort(a: var seq[int], lo, hi: int) =
  if lo >= hi: return
  let pivot = a[hi]
  var i = lo
  for j in lo ..< hi:
    if a[j] < pivot:
      swap(a[i], a[j])
      inc i
  swap(a[i], a[hi])
  quickSort(a, lo, i - 1)
  quickSort(a, i + 1, hi)

var a = @[10, 7, 8, 9, 1, 5, 3]
quickSort(a, 0, a.high)
echo "Sorted: ", a.join(" ")
