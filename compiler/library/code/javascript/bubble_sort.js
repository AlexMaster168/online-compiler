// Сортировка пузырьком: O(n^2). Если за проход не было обменов — массив уже отсортирован.
function bubbleSort(input) {
  const a = [...input];
  for (let i = 0; i < a.length - 1; i++) {
    let swapped = false;
    for (let j = 0; j < a.length - 1 - i; j++) {
      if (a[j] > a[j + 1]) {
        [a[j], a[j + 1]] = [a[j + 1], a[j]];
        swapped = true;
      }
    }
    if (!swapped) break;
  }
  return a;
}

console.log("Sorted: " + bubbleSort([5, 2, 9, 1, 5, 6]).join(" "));
