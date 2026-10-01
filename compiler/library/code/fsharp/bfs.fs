// Поиск в ширину: очередь — System.Collections.Generic.Queue из .NET.
open System.Collections.Generic

let graph = [| [ 1; 2 ]; [ 0; 3 ]; [ 0; 4 ]; [ 1; 5 ]; [ 2; 5 ]; [ 3; 4 ] |]
let dist = Array.create graph.Length -1
let order = ResizeArray<int>()
let queue = Queue<int>()
dist.[0] <- 0
queue.Enqueue 0
while queue.Count > 0 do
    let v = queue.Dequeue()
    order.Add v
    for u in graph.[v] do
        if dist.[u] = -1 then
            dist.[u] <- dist.[v] + 1
            queue.Enqueue u

printfn "BFS order: %s" (order |> Seq.map string |> String.concat " ")
printfn "Distances: %s" (dist |> Array.map string |> String.concat " ")
