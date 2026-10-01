// Быстрая сортировка (разбиение Ломуто): в среднем O(n log n), в худшем O(n^2).
void swap(List<int> a, int i, int j) {
  final t = a[i];
  a[i] = a[j];
  a[j] = t;
}

int partition(List<int> a, int lo, int hi) {
  final pivot = a[hi];
  var i = lo;
  for (var j = lo; j < hi; j++) {
    if (a[j] < pivot) {
      swap(a, i, j);
      i++;
    }
  }
  swap(a, i, hi);
  return i;
}

void quickSort(List<int> a, int lo, int hi) {
  if (lo >= hi) return;
  final p = partition(a, lo, hi);
  quickSort(a, lo, p - 1);
  quickSort(a, p + 1, hi);
}

void main() {
  final a = [10, 7, 8, 9, 1, 5, 3];
  quickSort(a, 0, a.length - 1);
  print('Sorted: ${a.join(' ')}');
}
