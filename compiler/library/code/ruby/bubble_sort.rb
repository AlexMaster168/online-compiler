# Сортировка пузырьком: O(n^2). Если за проход не было обменов — массив уже отсортирован.
def bubble_sort(input)
  a = input.dup
  (a.size - 1).times do |i|
    swapped = false
    (a.size - 1 - i).times do |j|
      next unless a[j] > a[j + 1]

      a[j], a[j + 1] = a[j + 1], a[j]
      swapped = true
    end
    break unless swapped
  end
  a
end

puts "Sorted: #{bubble_sort([5, 2, 9, 1, 5, 6]).join(' ')}"
