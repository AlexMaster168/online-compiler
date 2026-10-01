(* Поиск в глубину: список посещённых протягиваем через List.fold_left. *)
let graph = [| [ 1; 2 ]; [ 0; 3 ]; [ 0; 4 ]; [ 1; 5 ]; [ 2; 5 ]; [ 3; 4 ] |]

let rec dfs visited v = if List.mem v visited then visited else List.fold_left dfs (v :: visited) graph.(v)

let () =
  let order = List.rev (dfs [] 0) in
  print_endline ("DFS order: " ^ String.concat " " (List.map string_of_int order))
