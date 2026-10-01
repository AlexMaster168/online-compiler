(* Рюкзак 0/1: свёртка по предметам, каждая строка dp строится из предыдущей. *)
let knapsack items capacity =
  let dp =
    List.fold_left
      (fun dp (w, v) -> Array.init (capacity + 1) (fun c -> if c >= w then max dp.(c) (dp.(c - w) + v) else dp.(c)))
      (Array.make (capacity + 1) 0)
      items
  in
  dp.(capacity)

let () = Printf.printf "Knapsack max value: %d\n" (knapsack [ (1, 1); (3, 4); (4, 5); (5, 7) ] 7)
