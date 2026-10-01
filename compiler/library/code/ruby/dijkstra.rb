# Дейкстра за O(V^2): каждый раз берём ближайшую непосещённую вершину.
EDGES = [[[1, 4], [2, 1]], [[3, 1]], [[1, 2], [3, 5]], [[4, 3]], []].freeze

def dijkstra(start)
  dist = Array.new(EDGES.size, Float::INFINITY)
  done = Array.new(EDGES.size, false)
  dist[start] = 0
  EDGES.size.times do
    v = (0...EDGES.size).reject { |i| done[i] }.min_by { |i| dist[i] }
    break if dist[v] == Float::INFINITY

    done[v] = true
    EDGES[v].each { |u, w| dist[u] = [dist[u], dist[v] + w].min }
  end
  dist
end

puts "Dijkstra from 0: #{dijkstra(0).join(' ')}"
