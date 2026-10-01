// Решето Эратосфена: O(n log log n).
object Main:
  def sieve(n: Int): Seq[Int] =
    val isPrime = Array.fill(n + 1)(true)
    isPrime(0) = false
    isPrime(1) = false
    for p <- 2 to n if p * p <= n && isPrime(p); k <- p * p to n by p do isPrime(k) = false
    (0 to n).filter(isPrime)

  def main(args: Array[String]): Unit =
    println("Primes up to 50: " + sieve(50).mkString(" "))
