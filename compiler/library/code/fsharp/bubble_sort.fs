// Сортировка пузырьком: O(n^2). <- — присваивание элементу массива.
let bubbleSort (input: int[]) =
    let a = Array.copy input
    let mutable sorted = false
    let mutable i = 0
    while not sorted do
        sorted <- true
        for j in 0 .. a.Length - 2 - i do
            if a.[j] > a.[j + 1] then
                let t = a.[j]
                a.[j] <- a.[j + 1]
                a.[j + 1] <- t
                sorted <- false
        i <- i + 1
    a

bubbleSort [| 5; 2; 9; 1; 5; 6 |]
|> Array.map string
|> String.concat " "
|> printfn "Sorted: %s"
