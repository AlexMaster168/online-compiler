! Поиск в ширину: очередь на массиве. Вершины 0..5 хранятся в массивах с индексом 0.
program bfs
  implicit none
  integer, parameter :: adj(0:1, 0:5) = reshape([1, 2, 0, 3, 0, 4, 1, 5, 2, 5, 3, 4], [2, 6])
  integer :: dist(0:5), queue(6), order(6), head, tail, v, u, k

  dist = -1
  dist(0) = 0
  queue(1) = 0
  head = 1
  tail = 1
  do while (head <= tail)
    v = queue(head)
    order(head) = v
    head = head + 1
    do k = 0, 1
      u = adj(k, v)
      if (dist(u) == -1) then
        dist(u) = dist(v) + 1
        tail = tail + 1
        queue(tail) = u
      end if
    end do
  end do
  write(*, '(a, *(1x, i0))') 'BFS order:', order
  write(*, '(a, *(1x, i0))') 'Distances:', dist
end program bfs
