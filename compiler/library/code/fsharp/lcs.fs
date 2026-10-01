// Наибольшая общая подпоследовательность: Array2D — двумерный массив dp.
let lcs (a: string) (b: string) =
    let dp = Array2D.zeroCreate (a.Length + 1) (b.Length + 1)
    for i in 1 .. a.Length do
        for j in 1 .. b.Length do
            dp.[i, j] <-
                if a.[i - 1] = b.[j - 1] then dp.[i - 1, j - 1] + 1
                else max dp.[i - 1, j] dp.[i, j - 1]
    dp.[a.Length, b.Length]

printfn "LCS(ABCBDAB, BDCABA) = %d" (lcs "ABCBDAB" "BDCABA")
