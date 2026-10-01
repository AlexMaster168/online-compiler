# Поиск в глубину рекурсией: Set посещённых.
GRAPH = [[1, 2], [0, 3], [0, 4], [1, 5], [2, 5], [3, 4]]

def dfs(v : Int32, visited = Set(Int32).new, order = [] of Int32) : Array(Int32)
  visited << v
  order << v
  GRAPH[v].each { |u| dfs(u, visited, order) unless visited.includes?(u) }
  order
end

puts "DFS order: #{dfs(0).join(" ")}"
