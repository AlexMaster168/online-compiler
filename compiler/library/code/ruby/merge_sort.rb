# Сортировка слиянием: всегда O(n log n), стабильная.
def merge_sort(a)
  return a if a.size <= 1

  mid = a.size / 2
  left = merge_sort(a[0...mid])
  right = merge_sort(a[mid..])
  merged = []
  merged << (left.first <= right.first ? left.shift : right.shift) until left.empty? || right.empty?
  merged + left + right
end

puts "Sorted: #{merge_sort([38, 27, 43, 3, 9, 82, 10]).join(' ')}"
