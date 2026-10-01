# Сортировка слиянием: всегда O(n log n), стабильная.
def merge_sort(a : Array(Int32)) : Array(Int32)
  return a if a.size <= 1
  mid = a.size // 2
  left = merge_sort(a[0, mid])
  right = merge_sort(a[mid..])
  merged = [] of Int32
  i = j = 0
  while i < left.size && j < right.size
    if left[i] <= right[j]
      merged << left[i]; i += 1
    else
      merged << right[j]; j += 1
    end
  end
  merged + left[i..] + right[j..]
end

puts "Sorted: #{merge_sort([38, 27, 43, 3, 9, 82, 10]).join(" ")}"
