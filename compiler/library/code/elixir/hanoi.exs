# Ханойские башни: функция возвращает список ходов, печать — отдельно.
defmodule Hanoi do
  def moves(0, _source, _spare, _target), do: []

  def moves(n, source, spare, target) do
    moves(n - 1, source, target, spare) ++ [{n, source, target}] ++ moves(n - 1, spare, source, target)
  end
end

moves = Hanoi.moves(3, "A", "B", "C")
Enum.each(moves, fn {n, from, to} -> IO.puts("Move disk #{n} from #{from} to #{to}") end)
IO.puts("Total moves: #{length(moves)}")
