// Поиск в глубину: множество посещённых протягиваем через List.fold — без изменяемого состояния.
let graph = [| [ 1; 2 ]; [ 0; 3 ]; [ 0; 4 ]; [ 1; 5 ]; [ 2; 5 ]; [ 3; 4 ] |]

let rec dfs visited v =
    if List.contains v visited then visited
    else List.fold dfs (v :: visited) graph.[v]

dfs [] 0 |> List.rev |> List.map string |> String.concat " " |> printfn "DFS order: %s"
