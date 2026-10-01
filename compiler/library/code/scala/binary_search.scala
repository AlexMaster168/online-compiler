// Бинарный поиск: хвостовая рекурсия (@tailrec гарантирует, что компилятор сделает из неё цикл).
import scala.annotation.tailrec

object Main:
  def binarySearch(a: IndexedSeq[Int], target: Int): Option[Int] =
    @tailrec
    def go(lo: Int, hi: Int): Option[Int] =
      if lo > hi then None
      else
        val mid = (lo + hi) >>> 1
        if a(mid) == target then Some(mid)
        else if a(mid) < target then go(mid + 1, hi)
        else go(lo, mid - 1)
    go(0, a.length - 1)

  def main(args: Array[String]): Unit =
    val arr = Vector(1, 3, 5, 7, 9, 11, 13, 15, 17, 19)
    for target <- List(7, 4) do
      binarySearch(arr, target) match
        case Some(i) => println(s"Found $target at index $i")
        case None => println(s"$target not found")
