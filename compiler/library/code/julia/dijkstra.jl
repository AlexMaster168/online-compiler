# Дейкстра за O(V^2) на матрице весов (0 — нет ребра). argmin среди необработанных вершин.
w = [0 4 1 0 0
     0 0 0 1 0
     0 2 0 5 0
     0 0 0 0 3
     0 0 0 0 0]

n = size(w, 1)
dist = fill(typemax(Int), n)
done = falses(n)
dist[1] = 0
for _ in 1:n
    candidates = findall(.!done)
    v = candidates[argmin(dist[candidates])]
    dist[v] == typemax(Int) && break
    done[v] = true
    for u in 1:n
        if w[v, u] > 0 && dist[v] + w[v, u] < dist[u]
            dist[u] = dist[v] + w[v, u]
        end
    end
end
println("Dijkstra from 0: ", join(dist, " "))
