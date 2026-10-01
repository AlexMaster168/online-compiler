-- Поиск в глубину рекурсией: O(V + E).
local graph = {[0] = {1, 2}, {0, 3}, {0, 4}, {1, 5}, {2, 5}, {3, 4}}
local visited, order = {}, {}

local function dfs(v)
  visited[v] = true
  order[#order + 1] = v
  for _, u in ipairs(graph[v]) do
    if not visited[u] then dfs(u) end
  end
end

dfs(0)
print("DFS order: " .. table.concat(order, " "))
