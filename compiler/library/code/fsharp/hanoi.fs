// Ханойские башни: функция возвращает список ходов, печать — отдельно.
let rec hanoi n source spare target =
    if n = 0 then []
    else hanoi (n - 1) source target spare @ [ n, source, target ] @ hanoi (n - 1) spare source target

let moves = hanoi 3 'A' 'B' 'C'
for (n, from, ``to``) in moves do
    printfn "Move disk %d from %c to %c" n from ``to``
printfn "Total moves: %d" moves.Length
