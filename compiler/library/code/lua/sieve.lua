-- Решето Эратосфена: O(n log log n).
local function sieve(n)
  local composite, primes = {}, {}
  for p = 2, n do
    if not composite[p] then
      primes[#primes + 1] = p
      for k = p * p, n, p do composite[k] = true end
    end
  end
  return primes
end

print("Primes up to 50: " .. table.concat(sieve(50), " "))
