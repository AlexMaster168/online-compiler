# Решето Эратосфена: O(n log log n).
def sieve(n)
  is_prime = Array.new(n + 1, true)
  is_prime[0] = is_prime[1] = false
  (2..Integer.sqrt(n)).each do |p|
    next unless is_prime[p]

    (p * p).step(n, p) { |k| is_prime[k] = false }
  end
  (0..n).select { |i| is_prime[i] }
end

puts "Primes up to 50: #{sieve(50).join(' ')}"
