// Сортировка слиянием: всегда O(n log n), стабильная.
List<int> mergeSort(List<int> a) {
  if (a.length <= 1) return a;
  final mid = a.length ~/ 2;
  final left = mergeSort(a.sublist(0, mid));
  final right = mergeSort(a.sublist(mid));
  final merged = <int>[];
  var i = 0, j = 0;
  while (i < left.length && j < right.length) {
    merged.add(left[i] <= right[j] ? left[i++] : right[j++]);
  }
  return [...merged, ...left.sublist(i), ...right.sublist(j)];
}

void main() {
  print('Sorted: ${mergeSort([38, 27, 43, 3, 9, 82, 10]).join(' ')}');
}
