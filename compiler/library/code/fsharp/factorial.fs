// Факториал рекурсией. bigint — длинная арифметика, суффикс I у литералов.
let rec factorial (n: bigint) = if n <= 1I then 1I else n * factorial (n - 1I)

printfn "10! = %A" (factorial 10I)
printfn "20! = %A" (factorial 20I)
