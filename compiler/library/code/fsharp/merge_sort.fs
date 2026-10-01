// Сортировка слиянием: слияние — сопоставление с образцом по паре списков.
let rec merge xs ys =
    match xs, ys with
    | [], _ -> ys
    | _, [] -> xs
    | x :: xt, y :: _ when x <= y -> x :: merge xt ys
    | _, y :: yt -> y :: merge xs yt

let rec mergeSort list =
    match list with
    | [] | [ _ ] -> list
    | _ ->
        let left, right = List.splitAt (List.length list / 2) list
        merge (mergeSort left) (mergeSort right)

[ 38; 27; 43; 3; 9; 82; 10 ]
|> mergeSort
|> List.map string
|> String.concat " "
|> printfn "Sorted: %s"
