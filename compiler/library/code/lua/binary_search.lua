-- Бинарный поиск: O(log n). Возвращаем индекс с нуля, как в других языках.
local function binary_search(a, target)
  local lo, hi = 1, #a
  while lo <= hi do
    local mid = (lo + hi) // 2
    if a[mid] == target then return mid - 1 end
    if a[mid] < target then lo = mid + 1 else hi = mid - 1 end
  end
  return nil
end

local arr = {1, 3, 5, 7, 9, 11, 13, 15, 17, 19}
for _, target in ipairs({7, 4}) do
  local i = binary_search(arr, target)
  if i then
    print(string.format("Found %d at index %d", target, i))
  else
    print(target .. " not found")
  end
end
