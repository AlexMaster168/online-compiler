# Быстрое возведение в степень: O(log n). (Есть встроенный Integer#pow(exp, mod).)
MOD = 1_000_000_007

def power_mod(base, exp, mod)
  result = 1
  base %= mod
  while exp.positive?
    result = result * base % mod if exp.odd?
    base = base * base % mod
    exp >>= 1
  end
  result
end

puts "2^30 mod #{MOD} = #{power_mod(2, 30, MOD)}"
puts "3^200 mod #{MOD} = #{power_mod(3, 200, MOD)}"
