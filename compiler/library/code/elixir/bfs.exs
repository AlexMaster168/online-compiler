# Поиск в ширину на :queue из Erlang. Состояние (очередь, расстояния, порядок) — аргументы рекурсии.
defmodule BFS do
  @graph %{0 => [1, 2], 1 => [0, 3], 2 => [0, 4], 3 => [1, 5], 4 => [2, 5], 5 => [3, 4]}

  def run(start), do: loop(:queue.from_list([start]), %{start => 0}, [])

  defp loop(queue, dist, order) do
    case :queue.out(queue) do
      {:empty, _} ->
        {Enum.reverse(order), dist}

      {{:value, v}, rest} ->
        new = Enum.reject(@graph[v], &Map.has_key?(dist, &1))
        dist = Enum.reduce(new, dist, &Map.put(&2, &1, dist[v] + 1))
        loop(Enum.reduce(new, rest, &:queue.in/2), dist, [v | order])
    end
  end
end

{order, dist} = BFS.run(0)
IO.puts("BFS order: " <> Enum.join(order, " "))
IO.puts("Distances: " <> Enum.map_join(0..5, " ", &dist[&1]))
