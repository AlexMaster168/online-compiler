// Факториал рекурсией. BigInt — длинная арифметика, переполнения не будет при любом n.
object Main:
  def factorial(n: Int): BigInt = if n <= 1 then 1 else n * factorial(n - 1)

  def main(args: Array[String]): Unit =
    println(s"10! = ${factorial(10)}")
    println(s"20! = ${factorial(20)}")
