// Рюкзак 0/1: свёртка по предметам, каждая строка dp строится из предыдущей.
let knapsack items capacity =
    items
    |> List.fold
        (fun (dp: int[]) (w, v) -> Array.init (capacity + 1) (fun c -> if c >= w then max dp.[c] (dp.[c - w] + v) else dp.[c]))
        (Array.zeroCreate (capacity + 1))
    |> Array.last

printfn "Knapsack max value: %d" (knapsack [ 1, 1; 3, 4; 4, 5; 5, 7 ] 7)
