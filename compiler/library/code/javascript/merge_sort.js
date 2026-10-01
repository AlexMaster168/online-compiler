// Сортировка слиянием: всегда O(n log n), стабильная.
function mergeSort(a) {
  if (a.length <= 1) return a;
  const mid = a.length >> 1;
  const left = mergeSort(a.slice(0, mid));
  const right = mergeSort(a.slice(mid));
  const merged = [];
  let i = 0, j = 0;
  while (i < left.length && j < right.length) {
    merged.push(left[i] <= right[j] ? left[i++] : right[j++]);
  }
  return merged.concat(left.slice(i), right.slice(j));
}

console.log("Sorted: " + mergeSort([38, 27, 43, 3, 9, 82, 10]).join(" "));
