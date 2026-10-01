# Числа Фибоначчи ленивым потоком Stream.unfold. Целые в Elixir безразмерные.
fibs = Stream.unfold({0, 1}, fn {a, b} -> {a, {b, a + b}} end)

IO.puts("Fibonacci: " <> Enum.join(Enum.take(fibs, 15), " "))
IO.puts("F(50) = #{Enum.at(fibs, 50)}")
