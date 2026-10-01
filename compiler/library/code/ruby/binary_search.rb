# Бинарный поиск: O(log n). (У Array есть bsearch — пишем руками.)
def binary_search(a, target)
  lo = 0
  hi = a.size - 1
  while lo <= hi
    mid = (lo + hi) / 2
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
  i = binary_search(arr, target)
  puts i ? "Found #{target} at index #{i}" : "#{target} not found"
end
