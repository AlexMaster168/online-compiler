// Быстрая сортировка в функциональном стиле: опора — голова списка, List.partition делит хвост.
let rec quickSort list =
    match list with
    | [] -> []
    | pivot :: rest ->
        let smaller, larger = List.partition (fun x -> x < pivot) rest
        quickSort smaller @ [ pivot ] @ quickSort larger

[ 10; 7; 8; 9; 1; 5; 3 ]
|> quickSort
|> List.map string
|> String.concat " "
|> printfn "Sorted: %s"
