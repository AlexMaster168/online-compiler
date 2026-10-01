# НОД по Евклиду: несколько клауз функции вместо if.
defmodule MathEx do
  def gcd(a, 0), do: a
  def gcd(a, b), do: gcd(b, rem(a, b))

  def lcm(a, b), do: div(a, gcd(a, b)) * b
end

IO.puts("GCD(48, 18) = #{MathEx.gcd(48, 18)}")
IO.puts("LCM(48, 18) = #{MathEx.lcm(48, 18)}")
