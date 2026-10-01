# Бинарный поиск: O(log n). Option из std/options — Some(i) или none.
import std/options

proc binarySearch(a: openArray[int], target: int): Option[int] =
  var lo = 0
  var hi = a.high
  while lo <= hi:
    let mid = (lo + hi) div 2
    if a[mid] == target: return some(mid)
    if a[mid] < target: lo = mid + 1 else: hi = mid - 1
  none(int)

let arr = [1, 3, 5, 7, 9, 11, 13, 15, 17, 19]
for target in [7, 4]:
  let i = binarySearch(arr, target)
  if i.isSome: echo "Found ", target, " at index ", i.get
  else: echo target, " not found"
