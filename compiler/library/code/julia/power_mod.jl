# Быстрое возведение в степень: O(log n). (Есть встроенный powermod — пишем руками.)
const MOD = 1_000_000_007

function power_mod(base, exp, m)
    result = 1
    base %= m
    while exp > 0
        isodd(exp) && (result = result * base % m)
        base = base * base % m
        exp >>= 1
    end
    result
end

println("2^30 mod $MOD = ", power_mod(2, 30, MOD))
println("3^200 mod $MOD = ", power_mod(3, 200, MOD))
