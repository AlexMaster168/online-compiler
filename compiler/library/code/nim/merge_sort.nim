# Сортировка слиянием: срезы a[0 ..< mid] копируют половины, результат собираем в новую seq.
import std/strutils

proc mergeSort(a: seq[int]): seq[int] =
  if a.len <= 1: return a
  let mid = a.len div 2
  let left = mergeSort(a[0 ..< mid])
  let right = mergeSort(a[mid .. ^1])
  var i, j = 0
  while i < left.len and j < right.len:
    if left[i] <= right[j]:
      result.add left[i]; inc i
    else:
      result.add right[j]; inc j
  result.add left[i .. ^1]
  result.add right[j .. ^1]

echo "Sorted: ", mergeSort(@[38, 27, 43, 3, 9, 82, 10]).join(" ")
