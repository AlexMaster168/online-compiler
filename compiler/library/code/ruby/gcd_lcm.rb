# НОД по Евклиду: gcd(a, b) = gcd(b, a mod b). (У Integer есть встроенные gcd/lcm — пишем руками.)
def gcd(a, b)
  b.zero? ? a : gcd(b, a % b)
end

def lcm(a, b)
  a / gcd(a, b) * b
end

puts "GCD(48, 18) = #{gcd(48, 18)}"
puts "LCM(48, 18) = #{lcm(48, 18)}"
