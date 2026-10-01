// НОД по Евклиду: рекурсивная функция (let rec), хвостовой вызов F# превращает в цикл.
let rec gcd a b = if b = 0L then a else gcd b (a % b)
let lcm a b = a / gcd a b * b

printfn "GCD(48, 18) = %d" (gcd 48L 18L)
printfn "LCM(48, 18) = %d" (lcm 48L 18L)
