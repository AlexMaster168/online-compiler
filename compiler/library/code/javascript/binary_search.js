// Бинарный поиск: O(log n), массив обязан быть отсортирован.
function binarySearch(a, target) {
  let lo = 0, hi = a.length - 1;
  while (lo <= hi) {
    const mid = (lo + hi) >> 1;
    if (a[mid] === target) return mid;
    if (a[mid] < target) lo = mid + 1;
    else hi = mid - 1;
  }
  return -1;
}

const arr = [1, 3, 5, 7, 9, 11, 13, 15, 17, 19];
for (const target of [7, 4]) {
  const i = binarySearch(arr, target);
  console.log(i >= 0 ? `Found ${target} at index ${i}` : `${target} not found`);
}
