// Рюкзак 0/1: свёртка по предметам, каждая строка dp строится из предыдущей.
object Main:
  def knapsack(items: List[(Int, Int)], capacity: Int): Int =
    items
      .foldLeft(Vector.fill(capacity + 1)(0)) { case (dp, (w, v)) =>
        Vector.tabulate(capacity + 1)(c => if c >= w then math.max(dp(c), dp(c - w) + v) else dp(c))
      }
      .last

  def main(args: Array[String]): Unit =
    println("Knapsack max value: " + knapsack(List(1 -> 1, 3 -> 4, 4 -> 5, 5 -> 7), 7))
