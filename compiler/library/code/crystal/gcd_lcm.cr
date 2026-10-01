# НОД по Евклиду. (У Int есть встроенные gcd/lcm — пишем свои.)
def gcd(a : Int64, b : Int64) : Int64
  b == 0 ? a : gcd(b, a % b)
end

def lcm(a : Int64, b : Int64) : Int64
  a // gcd(a, b) * b
end

puts "GCD(48, 18) = #{gcd(48_i64, 18_i64)}"
puts "LCM(48, 18) = #{lcm(48_i64, 18_i64)}"
