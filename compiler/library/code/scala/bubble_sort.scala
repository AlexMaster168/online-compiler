// Сортировка пузырьком: O(n^2). boundary.break — выход из цикла в Scala 3 (обычного break нет).
import scala.util.boundary, boundary.break

object Main:
  def bubbleSort(input: Array[Int]): Array[Int] =
    val a = input.clone()
    boundary:
      for i <- 0 until a.length - 1 do
        var swapped = false
        for j <- 0 until a.length - 1 - i do
          if a(j) > a(j + 1) then
            val t = a(j); a(j) = a(j + 1); a(j + 1) = t
            swapped = true
        if !swapped then break()
    a

  def main(args: Array[String]): Unit =
    println("Sorted: " + bubbleSort(Array(5, 2, 9, 1, 5, 6)).mkString(" "))
