// Дейкстра с PriorityQueue из .NET 6+: O((V + E) log V).
open System.Collections.Generic

let graph = [| [ 1, 4; 2, 1 ]; [ 3, 1 ]; [ 1, 2; 3, 5 ]; [ 4, 3 ]; [] |]
let dist = Array.create graph.Length System.Int32.MaxValue
let pq = PriorityQueue<int, int>()
dist.[0] <- 0
pq.Enqueue(0, 0)
let mutable v = 0
let mutable d = 0
while pq.TryDequeue(&v, &d) do
    if d <= dist.[v] then // иначе запись устарела
        for (u, w) in graph.[v] do
            if d + w < dist.[u] then
                dist.[u] <- d + w
                pq.Enqueue(u, dist.[u])

printfn "Dijkstra from 0: %s" (dist |> Array.map string |> String.concat " ")
