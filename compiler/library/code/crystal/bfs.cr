# Поиск в ширину: Deque — двусторонняя очередь из стандартной библиотеки.
GRAPH = [[1, 2], [0, 3], [0, 4], [1, 5], [2, 5], [3, 4]]

dist = Array.new(GRAPH.size, -1)
order = [] of Int32
queue = Deque{0}
dist[0] = 0
until queue.empty?
  v = queue.shift
  order << v
  GRAPH[v].each do |u|
    if dist[u] == -1
      dist[u] = dist[v] + 1
      queue << u
    end
  end
end

puts "BFS order: #{order.join(" ")}"
puts "Distances: #{dist.join(" ")}"
