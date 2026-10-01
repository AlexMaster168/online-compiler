(* Решето Эратосфена: O(n log log n). *)
let sieve n =
  let is_prime = Array.make (n + 1) true in
  is_prime.(0) <- false;
  is_prime.(1) <- false;
  for p = 2 to n do
    if is_prime.(p) && p * p <= n then begin
      let k = ref (p * p) in
      while !k <= n do
        is_prime.(!k) <- false;
        k := !k + p
      done
    end
  done;
  List.filter (fun i -> is_prime.(i)) (List.init (n + 1) Fun.id)

let () = print_endline ("Primes up to 50: " ^ String.concat " " (List.map string_of_int (sieve 50)))
