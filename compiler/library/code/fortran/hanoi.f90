! Ханойские башни: 2^n - 1 ходов.
module towers
  implicit none
  integer :: moves = 0
contains
  recursive subroutine hanoi(n, source, spare, target)
    integer, intent(in) :: n
    character, intent(in) :: source, spare, target
    if (n == 0) return
    call hanoi(n - 1, source, target, spare)
    write(*, '(a, i0, a, a, a, a)') 'Move disk ', n, ' from ', source, ' to ', target
    moves = moves + 1
    call hanoi(n - 1, spare, source, target)
  end subroutine hanoi
end module towers

program hanoi_demo
  use towers
  implicit none
  call hanoi(3, 'A', 'B', 'C')
  write(*, '(a, i0)') 'Total moves: ', moves
end program hanoi_demo
