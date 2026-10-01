! Дейкстра за O(V^2) на матрице весов (0 — нет ребра). minloc с маской находит ближайшую вершину.
program dijkstra
  implicit none
  integer, parameter :: n = 5
  integer :: w(0:n - 1, 0:n - 1), dist(0:n - 1), step, v, u
  logical :: done(0:n - 1)

  w = 0
  w(0, 1) = 4; w(0, 2) = 1; w(2, 1) = 2; w(1, 3) = 1; w(2, 3) = 5; w(3, 4) = 3
  dist = huge(0)
  dist(0) = 0
  done = .false.
  do step = 1, n
    v = minloc(dist, dim=1, mask=.not. done) - 1  ! minloc считает с 1
    if (dist(v) == huge(0)) exit
    done(v) = .true.
    do u = 0, n - 1
      if (w(v, u) > 0) dist(u) = min(dist(u), dist(v) + w(v, u))
    end do
  end do
  write(*, '(a, *(1x, i0))') 'Dijkstra from 0:', dist
end program dijkstra
