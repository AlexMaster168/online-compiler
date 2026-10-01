-- Числа Фибоначчи итеративно. В Lua 5.4 целые 64-битные — F(50) помещается.
local function fib(n)
  local a, b = 0, 1
  for _ = 1, n do a, b = b, a + b end
  return a
end

local first = {}
for i = 0, 14 do first[#first + 1] = fib(i) end
print("Fibonacci: " .. table.concat(first, " "))
print("F(50) = " .. fib(50))
