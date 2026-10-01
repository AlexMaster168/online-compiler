(* Числа Фибоначчи хвостовой рекурсией с аккумуляторами. int в OCaml — 63 бита, F(50) помещается. *)
let fib n =
  let rec go n a b = if n = 0 then a else go (n - 1) b (a + b) in
  go n 0 1

let () =
  let first = List.init 15 fib in
  print_endline ("Fibonacci: " ^ String.concat " " (List.map string_of_int first));
  Printf.printf "F(50) = %d\n" (fib 50)
