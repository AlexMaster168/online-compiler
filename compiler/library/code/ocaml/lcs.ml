(* Наибольшая общая подпоследовательность: Array.make_matrix — двумерный массив dp. *)
let lcs a b =
  let n = String.length a and m = String.length b in
  let dp = Array.make_matrix (n + 1) (m + 1) 0 in
  for i = 1 to n do
    for j = 1 to m do
      dp.(i).(j) <-
        (if a.[i - 1] = b.[j - 1] then dp.(i - 1).(j - 1) + 1 else max dp.(i - 1).(j) dp.(i).(j - 1))
    done
  done;
  dp.(n).(m)

let () = Printf.printf "LCS(ABCBDAB, BDCABA) = %d\n" (lcs "ABCBDAB" "BDCABA")
