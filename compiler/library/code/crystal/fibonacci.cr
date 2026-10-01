# Числа Фибоначчи итеративно. Литерал 0_i64 — сразу Int64, иначе F(50) переполнил бы Int32.
def fib(n : Int32) : Int64
  a, b = 0_i64, 1_i64
  n.times { a, b = b, a + b }
  a
end

puts "Fibonacci: #{(0...15).map { |i| fib(i) }.join(" ")}"
puts "F(50) = #{fib(50)}"
