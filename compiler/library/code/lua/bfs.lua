-- Поиск в ширину: очередь на таблице с указателем головы, O(V + E). Вершины 0..5, хранятся по ключу.
local graph = {[0] = {1, 2}, {0, 3}, {0, 4}, {1, 5}, {2, 5}, {3, 4}}

local dist, order, queue, head = {[0] = 0}, {}, {0}, 1
while head <= #queue do
  local v = queue[head]
  head = head + 1
  order[#order + 1] = v
  for _, u in ipairs(graph[v]) do
    if dist[u] == nil then
      dist[u] = dist[v] + 1
      queue[#queue + 1] = u
    end
  end
end

local d = {}
for v = 0, 5 do d[#d + 1] = dist[v] end
print("BFS order: " .. table.concat(order, " "))
print("Distances: " .. table.concat(d, " "))
