(* Быстрое возведение в степень: O(log n). Произведение < 2^60 — 63-битного int хватает. *)
let modulus = 1_000_000_007

let power_mod base exp m =
  let rec go b e acc =
    if e = 0 then acc
    else go (b * b mod m) (e lsr 1) (if e land 1 = 1 then acc * b mod m else acc)
  in
  go (base mod m) exp 1

let () =
  Printf.printf "2^30 mod %d = %d\n" modulus (power_mod 2 30 modulus);
  Printf.printf "3^200 mod %d = %d\n" modulus (power_mod 3 200 modulus)
