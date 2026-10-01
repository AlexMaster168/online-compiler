# Рюкзак 0/1: для каждого предмета строим новую строку dp из старой.
defmodule Knapsack do
  def best(items, capacity) do
    initial = Map.new(0..capacity, &{&1, 0})

    items
    |> Enum.reduce(initial, fn {w, v}, dp ->
      Map.new(0..capacity, fn c ->
        {c, if(c >= w, do: max(dp[c], dp[c - w] + v), else: dp[c])}
      end)
    end)
    |> Map.fetch!(capacity)
  end
end

IO.puts("Knapsack max value: #{Knapsack.best(Enum.zip([1, 3, 4, 5], [1, 4, 5, 7]), 7)}")
