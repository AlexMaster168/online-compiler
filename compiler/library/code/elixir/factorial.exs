# Факториал рекурсией с клаузами функции.
defmodule Fact do
  def of(0), do: 1
  def of(n) when n > 0, do: n * of(n - 1)
end

IO.puts("10! = #{Fact.of(10)}")
IO.puts("20! = #{Fact.of(20)}")
