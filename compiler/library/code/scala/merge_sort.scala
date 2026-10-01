// Сортировка слиянием на неизменяемых списках: слияние — рекурсия с сопоставлением с образцом.
object Main:
  def merge(xs: List[Int], ys: List[Int]): List[Int] = (xs, ys) match
    case (Nil, _) => ys
    case (_, Nil) => xs
    case (x :: xt, y :: yt) => if x <= y then x :: merge(xt, ys) else y :: merge(xs, yt)

  def mergeSort(xs: List[Int]): List[Int] =
    if xs.length <= 1 then xs
    else
      val (left, right) = xs.splitAt(xs.length / 2)
      merge(mergeSort(left), mergeSort(right))

  def main(args: Array[String]): Unit =
    println("Sorted: " + mergeSort(List(38, 27, 43, 3, 9, 82, 10)).mkString(" "))
