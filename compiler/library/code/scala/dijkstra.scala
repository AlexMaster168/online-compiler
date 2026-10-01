// Дейкстра с PriorityQueue: Ordering.by(-расстояние) превращает максимальную кучу в минимальную.
import scala.collection.mutable

object Main:
  val graph = Vector(List(1 -> 4, 2 -> 1), List(3 -> 1), List(1 -> 2, 3 -> 5), List(4 -> 3), Nil)

  def main(args: Array[String]): Unit =
    val dist = Array.fill(graph.size)(Int.MaxValue)
    val pq = mutable.PriorityQueue((0, 0))(Ordering.by((d: Int, _: Int) => -d))
    dist(0) = 0
    while pq.nonEmpty do
      val (d, v) = pq.dequeue()
      if d <= dist(v) then // иначе запись устарела
        for (u, w) <- graph(v) if d + w < dist(u) do
          dist(u) = d + w
          pq.enqueue((dist(u), u))
    println("Dijkstra from 0: " + dist.mkString(" "))
