(* Факториал рекурсией. 20! < 2^62 — помещается в 63-битный int OCaml. *)
let rec factorial n = if n <= 1 then 1 else n * factorial (n - 1)

let () =
  Printf.printf "10! = %d\n" (factorial 10);
  Printf.printf "20! = %d\n" (factorial 20)
