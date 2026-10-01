-- Быстрое возведение в степень: O(log n). Произведение < 2^63 — целых Lua 5.4 хватает.
local MOD = 1000000007

local function power_mod(base, exp, mod)
  local result = 1
  base = base % mod
  while exp > 0 do
    if exp & 1 == 1 then result = result * base % mod end
    base = base * base % mod
    exp = exp >> 1
  end
  return result
end

print(string.format("2^30 mod %d = %d", MOD, power_mod(2, 30, MOD)))
print(string.format("3^200 mod %d = %d", MOD, power_mod(3, 200, MOD)))
