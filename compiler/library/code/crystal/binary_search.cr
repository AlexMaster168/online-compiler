# Бинарный поиск: Int32? — «число или nil», компилятор заставит проверить nil.
def binary_search(a : Array(Int32), target : Int32) : Int32?
  lo, hi = 0, a.size - 1
  while lo <= hi
    mid = (lo + hi) // 2
    return mid if a[mid] == target
    if a[mid] < target
      lo = mid + 1
    else
      hi = mid - 1
    end
  end
  nil
end

arr = [1, 3, 5, 7, 9, 11, 13, 15, 17, 19]
[7, 4].each do |target|
  if i = binary_search(arr, target)
    puts "Found #{target} at index #{i}"
  else
    puts "#{target} not found"
  end
end
