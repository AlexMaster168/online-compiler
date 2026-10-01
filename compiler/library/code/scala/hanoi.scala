// Ханойские башни: функция возвращает список ходов, печать — отдельно.
object Main:
  def hanoi(n: Int, source: Char, spare: Char, target: Char): List[(Int, Char, Char)] =
    if n == 0 then Nil
    else hanoi(n - 1, source, target, spare) ++ List((n, source, target)) ++ hanoi(n - 1, spare, source, target)

  def main(args: Array[String]): Unit =
    val moves = hanoi(3, 'A', 'B', 'C')
    for (n, from, to) <- moves do println(s"Move disk $n from $from to $to")
    println(s"Total moves: ${moves.size}")
