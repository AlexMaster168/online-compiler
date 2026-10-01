# Быстрая сортировка (разбиение Ломуто) на месте.
def partition(a : Array(Int32), lo : Int32, hi : Int32) : Int32
  pivot = a[hi]
  i = lo
  (lo...hi).each do |j|
    if a[j] < pivot
      a.swap(i, j)
      i += 1
    end
  end
  a.swap(i, hi)
  i
end

def quick_sort(a : Array(Int32), lo = 0, hi = a.size - 1)
  return if lo >= hi
  p = partition(a, lo, hi)
  quick_sort(a, lo, p - 1)
  quick_sort(a, p + 1, hi)
end

data = [10, 7, 8, 9, 1, 5, 3]
quick_sort(data)
puts "Sorted: #{data.join(" ")}"
