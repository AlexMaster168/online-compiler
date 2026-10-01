// Быстрая сортировка (разбиение Ломуто) на месте: массив изменяемый, обмены через swap.
object Main:
  def swap(a: Array[Int], i: Int, j: Int): Unit =
    val t = a(i); a(i) = a(j); a(j) = t

  def quickSort(a: Array[Int], lo: Int, hi: Int): Unit =
    if lo < hi then
      val pivot = a(hi)
      var i = lo
      for j <- lo until hi if a(j) < pivot do
        swap(a, i, j)
        i += 1
      swap(a, i, hi)
      quickSort(a, lo, i - 1)
      quickSort(a, i + 1, hi)

  def main(args: Array[String]): Unit =
    val a = Array(10, 7, 8, 9, 1, 5, 3)
    quickSort(a, 0, a.length - 1)
    println("Sorted: " + a.mkString(" "))
