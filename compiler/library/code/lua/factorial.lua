-- Факториал рекурсией. 20! — предел 64-битного целого Lua 5.4.
local function factorial(n)
  if n <= 1 then return 1 end
  return n * factorial(n - 1)
end

print("10! = " .. factorial(10))
print("20! = " .. factorial(20))
