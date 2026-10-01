// Быстрая сортировка (разбиение Ломуто): в среднем O(n log n), в худшем O(n^2).
function partition(a, lo, hi) {
  const pivot = a[hi];
  let i = lo;
  for (let j = lo; j < hi; j++) {
    if (a[j] < pivot) {
      [a[i], a[j]] = [a[j], a[i]];
      i++;
    }
  }
  [a[i], a[hi]] = [a[hi], a[i]];
  return i;
}

function quickSort(a, lo = 0, hi = a.length - 1) {
  if (lo < hi) {
    const p = partition(a, lo, hi);
    quickSort(a, lo, p - 1);
    quickSort(a, p + 1, hi);
  }
  return a;
}

console.log("Sorted: " + quickSort([10, 7, 8, 9, 1, 5, 3]).join(" "));
