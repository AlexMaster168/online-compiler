# Быстрая сортировка (разбиение Ломуто): в среднем O(n log n), в худшем O(n^2).
def partition(a, lo, hi)
  pivot = a[hi]
  i = lo
  (lo...hi).each do |j|
    next unless a[j] < pivot

    a[i], a[j] = a[j], a[i]
    i += 1
  end
  a[i], a[hi] = a[hi], a[i]
  i
end

def quick_sort(a, lo = 0, hi = a.size - 1)
  return a if lo >= hi

  p = partition(a, lo, hi)
  quick_sort(a, lo, p - 1)
  quick_sort(a, p + 1, hi)
  a
end

puts "Sorted: #{quick_sort([10, 7, 8, 9, 1, 5, 3]).join(' ')}"
