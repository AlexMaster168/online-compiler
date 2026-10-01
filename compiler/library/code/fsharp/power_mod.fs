// Быстрое возведение в степень: рекурсия с аккумулятором, O(log n).
let modulus = 1_000_000_007L

let powerMod b e m =
    let rec go b e acc =
        if e = 0L then acc
        else
            let acc = if e % 2L = 1L then acc * b % m else acc
            go (b * b % m) (e / 2L) acc
    go (b % m) e 1L

printfn "2^30 mod %d = %d" modulus (powerMod 2L 30L modulus)
printfn "3^200 mod %d = %d" modulus (powerMod 3L 200L modulus)
