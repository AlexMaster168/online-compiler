// Поиск в глубину: множество посещённых протягиваем через foldLeft — без изменяемого состояния.
object Main:
  val graph = Vector(List(1, 2), List(0, 3), List(0, 4), List(1, 5), List(2, 5), List(3, 4))

  def dfs(v: Int, visited: Vector[Int]): Vector[Int] =
    if visited.contains(v) then visited
    else graph(v).foldLeft(visited :+ v)((acc, u) => dfs(u, acc))

  def main(args: Array[String]): Unit =
    println("DFS order: " + dfs(0, Vector.empty).mkString(" "))
