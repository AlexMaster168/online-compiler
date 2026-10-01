// Сортировка пузырьком: O(n^2). Если за проход не было обменов — массив уже отсортирован.
List<int> bubbleSort(List<int> input) {
  final a = [...input];
  for (var i = 0; i < a.length - 1; i++) {
    var swapped = false;
    for (var j = 0; j < a.length - 1 - i; j++) {
      if (a[j] > a[j + 1]) {
        final t = a[j];
        a[j] = a[j + 1];
        a[j + 1] = t;
        swapped = true;
      }
    }
    if (!swapped) break;
  }
  return a;
}

void main() {
  print('Sorted: ${bubbleSort([5, 2, 9, 1, 5, 6]).join(' ')}');
}
