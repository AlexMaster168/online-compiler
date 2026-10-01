# Поиск в ширину: очередь — вектор с popfirst!. Вершины 0..5 — ключи словаря.
graph = Dict(0 => [1, 2], 1 => [0, 3], 2 => [0, 4], 3 => [1, 5], 4 => [2, 5], 5 => [3, 4])

dist = Dict(0 => 0)
order = Int[]
queue = [0]
while !isempty(queue)
    v = popfirst!(queue)
    push!(order, v)
    for u in graph[v]
        if !haskey(dist, u)
            dist[u] = dist[v] + 1
            push!(queue, u)
        end
    end
end

println("BFS order: ", join(order, " "))
println("Distances: ", join((dist[v] for v in 0:5), " "))
