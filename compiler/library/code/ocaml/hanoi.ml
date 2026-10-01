(* Ханойские башни: функция возвращает число ходов, печатая их по пути. *)
let rec hanoi n source spare target =
  if n = 0 then 0
  else begin
    let before = hanoi (n - 1) source target spare in
    Printf.printf "Move disk %d from %c to %c\n" n source target;
    before + 1 + hanoi (n - 1) spare source target
  end

let () = Printf.printf "Total moves: %d\n" (hanoi 3 'A' 'B' 'C')
