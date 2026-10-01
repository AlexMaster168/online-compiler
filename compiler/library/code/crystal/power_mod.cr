# Быстрое возведение в степень: O(log n).
MOD = 1_000_000_007_i64

def power_mod(base : Int64, exp : Int64, m : Int64) : Int64
  result = 1_i64
  base %= m
  while exp > 0
    result = result * base % m if exp.odd?
    base = base * base % m
    exp >>= 1
  end
  result
end

puts "2^30 mod #{MOD} = #{power_mod(2_i64, 30_i64, MOD)}"
puts "3^200 mod #{MOD} = #{power_mod(3_i64, 200_i64, MOD)}"
