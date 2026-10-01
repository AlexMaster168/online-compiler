-- Дейкстра за O(V^2): каждый раз берём ближайшую непосещённую вершину.
local edges = {[0] = {{1, 4}, {2, 1}}, {{3, 1}}, {{1, 2}, {3, 5}}, {{4, 3}}, {}}
local n = 5
local dist, done = {}, {}
for v = 0, n - 1 do dist[v] = math.huge end
dist[0] = 0

for _ = 1, n do
  local v
  for i = 0, n - 1 do
    if not done[i] and (v == nil or dist[i] < dist[v]) then v = i end
  end
  if dist[v] == math.huge then break end
  done[v] = true
  for _, e in ipairs(edges[v]) do
    local u, w = e[1], e[2]
    if dist[v] + w < dist[u] then dist[u] = dist[v] + w end
  end
end

local out = {}
for v = 0, n - 1 do out[#out + 1] = dist[v] end
print("Dijkstra from 0: " .. table.concat(out, " "))
