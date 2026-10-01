// Поиск в ширину: изменяемая очередь из scala.collection.mutable.
import scala.collection.mutable

object Main:
  val graph = Vector(List(1, 2), List(0, 3), List(0, 4), List(1, 5), List(2, 5), List(3, 4))

  def main(args: Array[String]): Unit =
    val dist = Array.fill(graph.size)(-1)
    val order = mutable.ArrayBuffer.empty[Int]
    val queue = mutable.Queue(0)
    dist(0) = 0
    while queue.nonEmpty do
      val v = queue.dequeue()
      order += v
      for u <- graph(v) if dist(u) == -1 do
        dist(u) = dist(v) + 1
        queue.enqueue(u)
    println("BFS order: " + order.mkString(" "))
    println("Distances: " + dist.mkString(" "))
