(* НОД по Евклиду: рекурсия с сопоставлением с образцом. *)
let rec gcd a = function 0 -> a | b -> gcd b (a mod b)
let lcm a b = a / gcd a b * b

let () =
  Printf.printf "GCD(48, 18) = %d\n" (gcd 48 18);
  Printf.printf "LCM(48, 18) = %d\n" (lcm 48 18)
