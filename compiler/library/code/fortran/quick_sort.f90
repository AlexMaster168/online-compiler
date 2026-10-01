! Быстрая сортировка (разбиение Ломуто) рекурсивной подпрограммой.
module quick
  implicit none
contains
  recursive subroutine sort(a, lo, hi)
    integer, intent(inout) :: a(:)
    integer, intent(in) :: lo, hi
    integer :: pivot, i, j, t
    if (lo >= hi) return
    pivot = a(hi)
    i = lo
    do j = lo, hi - 1
      if (a(j) < pivot) then
        t = a(i); a(i) = a(j); a(j) = t
        i = i + 1
      end if
    end do
    t = a(i); a(i) = a(hi); a(hi) = t
    call sort(a, lo, i - 1)
    call sort(a, i + 1, hi)
  end subroutine sort
end module quick

program quick_sort
  use quick
  implicit none
  integer :: a(7) = [10, 7, 8, 9, 1, 5, 3]
  call sort(a, 1, size(a))
  write(*, '(a, *(1x, i0))') 'Sorted:', a
end program quick_sort
