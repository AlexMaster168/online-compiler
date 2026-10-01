# Сортировка пузырьком: Crystal похож на Ruby, но компилируется и типизирован статически.
def bubble_sort(input : Array(Int32)) : Array(Int32)
  a = input.dup
  (a.size - 1).times do |i|
    swapped = false
    (a.size - 1 - i).times do |j|
      if a[j] > a[j + 1]
        a.swap(j, j + 1)
        swapped = true
      end
    end
    break unless swapped
  end
  a
end

puts "Sorted: #{bubble_sort([5, 2, 9, 1, 5, 6]).join(" ")}"
