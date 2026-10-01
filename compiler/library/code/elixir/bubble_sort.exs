# Сортировка пузырьком: данные неизменяемые, поэтому каждый проход строит новый список.
defmodule Bubble do
  def sort(list) do
    case pass(list) do
      {sorted, false} -> sorted
      {next, true} -> sort(next)
    end
  end

  defp pass([a, b | rest]) when a > b do
    {tail, _} = pass([a | rest])
    {[b | tail], true}
  end

  defp pass([a | rest]) do
    {tail, swapped} = pass(rest)
    {[a | tail], swapped}
  end

  defp pass([]), do: {[], false}
end

IO.puts("Sorted: " <> Enum.join(Bubble.sort([5, 2, 9, 1, 5, 6]), " "))
