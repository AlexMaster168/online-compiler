! Сортировка слиянием: срезы массивов a(lo:mid) — встроенная фишка Fortran.
module merging
  implicit none
contains
  recursive subroutine sort(a)
    integer, intent(inout) :: a(:)
    integer :: tmp(size(a)), mid, i, j, k
    if (size(a) < 2) return
    mid = size(a) / 2
    call sort(a(1:mid))
    call sort(a(mid + 1:))
    i = 1; j = mid + 1; k = 1
    do while (i <= mid .and. j <= size(a))
      if (a(i) <= a(j)) then
        tmp(k) = a(i); i = i + 1
      else
        tmp(k) = a(j); j = j + 1
      end if
      k = k + 1
    end do
    if (i <= mid) tmp(k:) = a(i:mid)
    if (j <= size(a)) tmp(k:) = a(j:)
    a = tmp
  end subroutine sort
end module merging

program merge_sort
  use merging
  implicit none
  integer :: a(7) = [38, 27, 43, 3, 9, 82, 10]
  call sort(a)
  write(*, '(a, *(1x, i0))') 'Sorted:', a
end program merge_sort
