! Поиск в глубину рекурсией: O(V + E).
module graph_dfs
  implicit none
  integer, parameter :: adj(0:1, 0:5) = reshape([1, 2, 0, 3, 0, 4, 1, 5, 2, 5, 3, 4], [2, 6])
  logical :: visited(0:5) = .false.
  integer :: order(6), count = 0
contains
  recursive subroutine dfs(v)
    integer, intent(in) :: v
    integer :: k
    visited(v) = .true.
    count = count + 1
    order(count) = v
    do k = 0, 1
      if (.not. visited(adj(k, v))) call dfs(adj(k, v))
    end do
  end subroutine dfs
end module graph_dfs

program dfs_demo
  use graph_dfs
  implicit none
  call dfs(0)
  write(*, '(a, *(1x, i0))') 'DFS order:', order(1:count)
end program dfs_demo
