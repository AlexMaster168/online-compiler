# Решето Эратосфена: вычёркиваем кратные срезом с шагом is_prime[p*p:p:n] .= false.
function sieve(n)
    is_prime = trues(n)
    is_prime[1] = false
    for p in 2:isqrt(n)
        is_prime[p] && (is_prime[p*p:p:n] .= false)
    end
    findall(is_prime)
end

println("Primes up to 50: ", join(sieve(50), " "))
