# Поиск в глубину рекурсией: O(V + E).
require 'set'

GRAPH = [[1, 2], [0, 3], [0, 4], [1, 5], [2, 5], [3, 4]].freeze

def dfs(v, visited = Set.new, order = [])
  visited << v
  order << v
  GRAPH[v].each { |u| dfs(u, visited, order) unless visited.include?(u) }
  order
end

puts "DFS order: #{dfs(0).join(' ')}"
