# Поиск в глубину: множество посещённых протягиваем через Enum.reduce.
defmodule DFS do
  @graph %{0 => [1, 2], 1 => [0, 3], 2 => [0, 4], 3 => [1, 5], 4 => [2, 5], 5 => [3, 4]}

  def run(start) do
    {_visited, order} = visit(start, {MapSet.new(), []})
    Enum.reverse(order)
  end

  defp visit(v, {visited, order} = acc) do
    if MapSet.member?(visited, v) do
      acc
    else
      Enum.reduce(@graph[v], {MapSet.put(visited, v), [v | order]}, &visit/2)
    end
  end
end

IO.puts("DFS order: " <> Enum.join(DFS.run(0), " "))
