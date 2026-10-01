(* Поиск в ширину: Queue из стандартной библиотеки, O(V + E). *)
let graph = [| [ 1; 2 ]; [ 0; 3 ]; [ 0; 4 ]; [ 1; 5 ]; [ 2; 5 ]; [ 3; 4 ] |]

let () =
  let dist = Array.make (Array.length graph) (-1) in
  let order = ref [] in
  let queue = Queue.create () in
  dist.(0) <- 0;
  Queue.add 0 queue;
  while not (Queue.is_empty queue) do
    let v = Queue.pop queue in
    order := v :: !order;
    List.iter
      (fun u ->
        if dist.(u) = -1 then begin
          dist.(u) <- dist.(v) + 1;
          Queue.add u queue
        end)
      graph.(v)
  done;
  let show l = String.concat " " (List.map string_of_int l) in
  print_endline ("BFS order: " ^ show (List.rev !order));
  print_endline ("Distances: " ^ show (Array.to_list dist))
