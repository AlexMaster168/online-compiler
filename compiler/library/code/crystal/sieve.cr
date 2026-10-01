# Решето Эратосфена: step — шаг по диапазону.
def sieve(n : Int32) : Array(Int32)
  is_prime = Array.new(n + 1, true)
  is_prime[0] = is_prime[1] = false
  (2..Math.isqrt(n)).each do |p|
    next unless is_prime[p]
    (p * p).step(to: n, by: p) { |k| is_prime[k] = false }
  end
  (0..n).select { |i| is_prime[i] }
end

puts "Primes up to 50: #{sieve(50).join(" ")}"
