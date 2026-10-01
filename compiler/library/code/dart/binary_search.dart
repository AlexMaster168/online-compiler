// Бинарный поиск: O(log n). int? — null, если не нашли.
int? binarySearch(List<int> a, int target) {
  var lo = 0, hi = a.length - 1;
  while (lo <= hi) {
    final mid = (lo + hi) ~/ 2;
    if (a[mid] == target) return mid;
    if (a[mid] < target) {
      lo = mid + 1;
    } else {
      hi = mid - 1;
    }
  }
  return null;
}

void main() {
  const arr = [1, 3, 5, 7, 9, 11, 13, 15, 17, 19];
  for (final target in [7, 4]) {
    final i = binarySearch(arr, target);
    print(i != null ? 'Found $target at index $i' : '$target not found');
  }
}
