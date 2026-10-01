(* Дейкстра за O(V^2): на каждом шаге — ближайшая необработанная вершина. *)
let graph = [| [ (1, 4); (2, 1) ]; [ (3, 1) ]; [ (1, 2); (3, 5) ]; [ (4, 3) ]; [] |]

let () =
  let n = Array.length graph in
  let dist = Array.make n max_int and done_ = Array.make n false in
  dist.(0) <- 0;
  (try
     for _ = 1 to n do
       let v = ref (-1) in
       for i = 0 to n - 1 do
         if (not done_.(i)) && (!v = -1 || dist.(i) < dist.(!v)) then v := i
       done;
       if dist.(!v) = max_int then raise Exit; (* остальные недостижимы *)
       done_.(!v) <- true;
       List.iter (fun (u, w) -> if dist.(!v) + w < dist.(u) then dist.(u) <- dist.(!v) + w) graph.(!v)
     done
   with Exit -> ());
  print_endline ("Dijkstra from 0: " ^ String.concat " " (Array.to_list (Array.map string_of_int dist)))
