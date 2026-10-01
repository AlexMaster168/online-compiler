# Дейкстра за O(V^2): каждый раз берём ближайшую необработанную вершину.
EDGES = [[{1, 4}, {2, 1}], [{3, 1}], [{1, 2}, {3, 5}], [{4, 3}], [] of {Int32, Int32}]

dist = Array.new(EDGES.size, Int32::MAX)
done = Array.new(EDGES.size, false)
dist[0] = 0
EDGES.size.times do
  v = (0...EDGES.size).reject { |i| done[i] }.min_by { |i| dist[i] }
  break if dist[v] == Int32::MAX
  done[v] = true
  EDGES[v].each do |(u, w)|
    dist[u] = dist[v] + w if dist[v] + w < dist[u]
  end
end

puts "Dijkstra from 0: #{dist.join(" ")}"
