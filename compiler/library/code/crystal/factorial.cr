# Факториал рекурсией. UInt64 — 20! помещается; переполнение в Crystal — исключение.
def factorial(n : UInt64) : UInt64
  n <= 1 ? 1_u64 : n * factorial(n - 1)
end

puts "10! = #{factorial(10_u64)}"
puts "20! = #{factorial(20_u64)}"
