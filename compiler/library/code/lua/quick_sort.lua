-- Быстрая сортировка (разбиение Ломуто): в среднем O(n log n), в худшем O(n^2).
local function partition(a, lo, hi)
  local pivot, i = a[hi], lo
  for j = lo, hi - 1 do
    if a[j] < pivot then
      a[i], a[j] = a[j], a[i]
      i = i + 1
    end
  end
  a[i], a[hi] = a[hi], a[i]
  return i
end

local function quick_sort(a, lo, hi)
  if lo >= hi then return end
  local p = partition(a, lo, hi)
  quick_sort(a, lo, p - 1)
  quick_sort(a, p + 1, hi)
end

local data = {10, 7, 8, 9, 1, 5, 3}
quick_sort(data, 1, #data)
print("Sorted: " .. table.concat(data, " "))
