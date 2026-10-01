// Числа Фибоначчи ленивым списком LazyList: каждый элемент — сумма двух предыдущих.
object Main:
  val fibs: LazyList[BigInt] = BigInt(0) #:: BigInt(1) #:: fibs.zip(fibs.tail).map(_ + _)

  def main(args: Array[String]): Unit =
    println("Fibonacci: " + fibs.take(15).mkString(" "))
    println(s"F(50) = ${fibs(50)}")
