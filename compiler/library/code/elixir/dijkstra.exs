# Дейкстра за O(V^2): рекурсия по шагам, расстояния — Map.
defmodule Dijkstra do
  @graph %{0 => [{1, 4}, {2, 1}], 1 => [{3, 1}], 2 => [{1, 2}, {3, 5}], 3 => [{4, 3}], 4 => []}

  def run(start) do
    dist = Map.new(Map.keys(@graph), &{&1, :infinity}) |> Map.put(start, 0)
    loop(dist, MapSet.new(Map.keys(@graph)))
  end

  defp loop(dist, pending) do
    reachable = Enum.filter(pending, &(dist[&1] != :infinity))

    if reachable == [] do
      dist
    else
      v = Enum.min_by(reachable, &dist[&1])

      dist =
        Enum.reduce(@graph[v], dist, fn {u, w}, acc ->
          if acc[u] == :infinity or dist[v] + w < acc[u], do: Map.put(acc, u, dist[v] + w), else: acc
        end)

      loop(dist, MapSet.delete(pending, v))
    end
  end
end

dist = Dijkstra.run(0)
IO.puts("Dijkstra from 0: " <> Enum.map_join(0..4, " ", &dist[&1]))
