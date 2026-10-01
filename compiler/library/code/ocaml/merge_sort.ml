(* Сортировка слиянием: split раскладывает элементы поочерёдно в два списка. *)
let rec split = function
  | x :: y :: rest ->
      let a, b = split rest in
      (x :: a, y :: b)
  | rest -> (rest, [])

let rec merge xs ys =
  match (xs, ys) with
  | [], _ -> ys
  | _, [] -> xs
  | x :: xt, y :: _ when x <= y -> x :: merge xt ys
  | _, y :: yt -> y :: merge xs yt

let rec merge_sort = function
  | ([] | [ _ ]) as l -> l
  | l ->
      let a, b = split l in
      merge (merge_sort a) (merge_sort b)

let () =
  let sorted = merge_sort [ 38; 27; 43; 3; 9; 82; 10 ] in
  print_endline ("Sorted: " ^ String.concat " " (List.map string_of_int sorted))
