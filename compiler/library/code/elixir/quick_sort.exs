# Быстрая сортировка: опора — голова списка, остальное делим Enum.split_with. В среднем O(n log n).
defmodule Quick do
  def sort([]), do: []

  def sort([pivot | rest]) do
    {smaller, larger} = Enum.split_with(rest, &(&1 < pivot))
    sort(smaller) ++ [pivot] ++ sort(larger)
  end
end

IO.puts("Sorted: " <> Enum.join(Quick.sort([10, 7, 8, 9, 1, 5, 3]), " "))
