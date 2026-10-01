(* Быстрая сортировка: опора — голова списка, List.partition делит хвост. *)
let rec quick_sort = function
  | [] -> []
  | pivot :: rest ->
      let smaller, larger = List.partition (fun x -> x < pivot) rest in
      quick_sort smaller @ [ pivot ] @ quick_sort larger

let () =
  let sorted = quick_sort [ 10; 7; 8; 9; 1; 5; 3 ] in
  print_endline ("Sorted: " ^ String.concat " " (List.map string_of_int sorted))
