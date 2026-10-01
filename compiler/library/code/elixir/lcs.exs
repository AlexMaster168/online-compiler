# Наибольшая общая подпоследовательность: строим таблицу построчно, храним только предыдущую строку.
defmodule LCS do
  def length_of(a, b) do
    xs = String.graphemes(a)
    ys = String.graphemes(b)
    first_row = List.duplicate(0, length(ys) + 1)

    xs
    |> Enum.reduce(first_row, fn x, prev -> next_row(x, ys, prev) end)
    |> List.last()
  end

  defp next_row(x, ys, prev) do
    pairs = Enum.zip([ys, prev, tl(prev)])

    {row, _} =
      Enum.reduce(pairs, {[0], 0}, fn {y, diag, up}, {row, left} ->
        value = if x == y, do: diag + 1, else: max(up, left)
        {[value | row], value}
      end)

    Enum.reverse(row)
  end
end

IO.puts("LCS(ABCBDAB, BDCABA) = #{LCS.length_of("ABCBDAB", "BDCABA")}")
