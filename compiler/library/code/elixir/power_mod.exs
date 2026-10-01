# Быстрое возведение в степень: O(log n). Битовые операции — из модуля Bitwise.
defmodule PowerMod do
  import Bitwise

  def pow(base, exp, m), do: pow(rem(base, m), exp, m, 1)

  defp pow(_base, 0, _m, acc), do: acc

  defp pow(base, exp, m, acc) do
    acc = if (exp &&& 1) == 1, do: rem(acc * base, m), else: acc
    pow(rem(base * base, m), exp >>> 1, m, acc)
  end
end

mod = 1_000_000_007
IO.puts("2^30 mod #{mod} = #{PowerMod.pow(2, 30, mod)}")
IO.puts("3^200 mod #{mod} = #{PowerMod.pow(3, 200, mod)}")
