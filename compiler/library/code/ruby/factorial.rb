# Факториал рекурсией. В Ruby целые числа безразмерные — переполнения нет.
def factorial(n)
  n <= 1 ? 1 : n * factorial(n - 1)
end

puts "10! = #{factorial(10)}"
puts "20! = #{factorial(20)}"
