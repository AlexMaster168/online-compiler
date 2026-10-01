-- Сортировка слиянием: всегда O(n log n), стабильная.
local function merge_sort(a)
  if #a <= 1 then return a end
  local mid = #a // 2
  local left, right = {}, {}
  for i = 1, mid do left[#left + 1] = a[i] end
  for i = mid + 1, #a do right[#right + 1] = a[i] end
  left, right = merge_sort(left), merge_sort(right)
  local merged, i, j = {}, 1, 1
  while i <= #left and j <= #right do
    if left[i] <= right[j] then
      merged[#merged + 1] = left[i]; i = i + 1
    else
      merged[#merged + 1] = right[j]; j = j + 1
    end
  end
  for k = i, #left do merged[#merged + 1] = left[k] end
  for k = j, #right do merged[#merged + 1] = right[k] end
  return merged
end

print("Sorted: " .. table.concat(merge_sort({38, 27, 43, 3, 9, 82, 10}), " "))
