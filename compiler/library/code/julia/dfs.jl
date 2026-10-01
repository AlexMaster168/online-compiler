# Поиск в глубину рекурсией: Set посещённых, вектор порядка обхода.
graph = Dict(0 => [1, 2], 1 => [0, 3], 2 => [0, 4], 3 => [1, 5], 4 => [2, 5], 5 => [3, 4])

function dfs(v, visited=Set{Int}(), order=Int[])
    push!(visited, v)
    push!(order, v)
    for u in graph[v]
        u in visited || dfs(u, visited, order)
    end
    order
end

println("DFS order: ", join(dfs(0), " "))
