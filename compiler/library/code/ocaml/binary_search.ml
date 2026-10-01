(* Бинарный поиск: рекурсивная функция возвращает option (Some i / None). *)
let binary_search a target =
  let rec go lo hi =
    if lo > hi then None
    else
      let mid = (lo + hi) / 2 in
      if a.(mid) = target then Some mid
      else if a.(mid) < target then go (mid + 1) hi
      else go lo (mid - 1)
  in
  go 0 (Array.length a - 1)

let () =
  let arr = [| 1; 3; 5; 7; 9; 11; 13; 15; 17; 19 |] in
  List.iter
    (fun target ->
      match binary_search arr target with
      | Some i -> Printf.printf "Found %d at index %d\n" target i
      | None -> Printf.printf "%d not found\n" target)
    [ 7; 4 ]
