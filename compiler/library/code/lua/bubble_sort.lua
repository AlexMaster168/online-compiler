-- Сортировка пузырьком: O(n^2). Если за проход не было обменов — массив уже отсортирован.
-- В Lua таблицы индексируются с 1.
local function bubble_sort(a)
  local n = #a
  for i = 1, n - 1 do
    local swapped = false
    for j = 1, n - i do
      if a[j] > a[j + 1] then
        a[j], a[j + 1] = a[j + 1], a[j]
        swapped = true
      end
    end
    if not swapped then break end
  end
  return a
end

print("Sorted: " .. table.concat(bubble_sort({5, 2, 9, 1, 5, 6}), " "))
