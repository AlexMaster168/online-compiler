-- Ханойские башни: 2^n - 1 ходов. Возвращаем число ходов.
local function hanoi(n, source, spare, target)
  if n == 0 then return 0 end
  local before = hanoi(n - 1, source, target, spare)
  print(string.format("Move disk %d from %s to %s", n, source, target))
  return before + 1 + hanoi(n - 1, spare, source, target)
end

print("Total moves: " .. hanoi(3, "A", "B", "C"))
