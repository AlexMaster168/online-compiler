// Решето Эратосфена: O(n log log n).
let sieve n =
    let isPrime = Array.create (n + 1) true
    isPrime.[0] <- false
    isPrime.[1] <- false
    for p in 2 .. n do
        if isPrime.[p] && p * p <= n then
            for k in p * p .. p .. n do
                isPrime.[k] <- false
    [ for i in 0 .. n do if isPrime.[i] then yield i ]

sieve 50 |> List.map string |> String.concat " " |> printfn "Primes up to 50: %s"
