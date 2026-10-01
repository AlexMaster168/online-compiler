# Сортировка слиянием: всегда O(n log n), стабильная.
defmodule MergeSort do
  def sort(list) when length(list) <= 1, do: list

  def sort(list) do
    {left, right} = Enum.split(list, div(length(list), 2))
    merge(sort(left), sort(right))
  end

  defp merge([], right), do: right
  defp merge(left, []), do: left
  defp merge([x | xs], [y | _] = right) when x <= y, do: [x | merge(xs, right)]
  defp merge(left, [y | ys]), do: [y | merge(left, ys)]
end

IO.puts("Sorted: " <> Enum.join(MergeSort.sort([38, 27, 43, 3, 9, 82, 10]), " "))
