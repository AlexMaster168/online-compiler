# Поиск в ширину: массив как очередь (shift/push), O(V + E).
GRAPH = [[1, 2], [0, 3], [0, 4], [1, 5], [2, 5], [3, 4]].freeze

dist = Array.new(GRAPH.size, -1)
dist[0] = 0
order = []
queue = [0]
until queue.empty?
  v = queue.shift
  order << v
  GRAPH[v].each do |u|
    next unless dist[u] == -1

    dist[u] = dist[v] + 1
    queue << u
  end
end

puts "BFS order: #{order.join(' ')}"
puts "Distances: #{dist.join(' ')}"
