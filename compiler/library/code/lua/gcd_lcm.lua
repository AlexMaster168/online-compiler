-- НОД по Евклиду: gcd(a, b) = gcd(b, a mod b). // — целочисленное деление (Lua 5.3+).
local function gcd(a, b)
  while b ~= 0 do a, b = b, a % b end
  return a
end

local function lcm(a, b) return a // gcd(a, b) * b end

print(string.format("GCD(48, 18) = %d", gcd(48, 18)))
print(string.format("LCM(48, 18) = %d", lcm(48, 18)))
