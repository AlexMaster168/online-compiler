# Числа Фибоначчи ленивым Enumerator: числа генерируются по требованию.
fibonacci = Enumerator.new do |y|
  a, b = 0, 1
  loop do
    y << a
    a, b = b, a + b
  end
end

puts "Fibonacci: #{fibonacci.take(15).join(' ')}"
puts "F(50) = #{fibonacci.lazy.drop(50).first}"
