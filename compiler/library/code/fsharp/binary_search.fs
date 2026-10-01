// Бинарный поиск: рекурсивная внутренняя функция, результат — option (Some i / None).
let binarySearch (a: int[]) target =
    let rec go lo hi =
        if lo > hi then None
        else
            let mid = (lo + hi) / 2
            if a.[mid] = target then Some mid
            elif a.[mid] < target then go (mid + 1) hi
            else go lo (mid - 1)
    go 0 (a.Length - 1)

let arr = [| 1; 3; 5; 7; 9; 11; 13; 15; 17; 19 |]
for target in [ 7; 4 ] do
    match binarySearch arr target with
    | Some i -> printfn "Found %d at index %d" target i
    | None -> printfn "%d not found" target
