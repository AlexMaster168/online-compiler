// Числа Фибоначчи бесконечной последовательностью Seq.unfold. 64-битные int64.
let fibs = Seq.unfold (fun (a, b) -> Some(a, (b, a + b))) (0L, 1L)

fibs |> Seq.take 15 |> Seq.map string |> String.concat " " |> printfn "Fibonacci: %s"
printfn "F(50) = %d" (Seq.item 50 fibs)
