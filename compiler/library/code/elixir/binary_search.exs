# Бинарный поиск: списки в Elixir связные, поэтому берём кортеж — у него доступ по индексу O(1).
defmodule Search do
  def binary(tuple, target), do: binary(tuple, target, 0, tuple_size(tuple) - 1)

  defp binary(_tuple, _target, lo, hi) when lo > hi, do: nil

  defp binary(tuple, target, lo, hi) do
    mid = div(lo + hi, 2)

    case elem(tuple, mid) do
      ^target -> mid
      value when value < target -> binary(tuple, target, mid + 1, hi)
      _ -> binary(tuple, target, lo, mid - 1)
    end
  end
end

arr = List.to_tuple([1, 3, 5, 7, 9, 11, 13, 15, 17, 19])

for target <- [7, 4] do
  case Search.binary(arr, target) do
    nil -> IO.puts("#{target} not found")
    i -> IO.puts("Found #{target} at index #{i}")
  end
end
