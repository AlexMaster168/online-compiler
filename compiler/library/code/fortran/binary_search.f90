! Бинарный поиск: O(log n). Индексы Fortran с 1 — печатаем с 0, как остальные языки.
program binary_search
  implicit none
  integer, parameter :: arr(10) = [1, 3, 5, 7, 9, 11, 13, 15, 17, 19]
  integer :: targets(2) = [7, 4], k, i

  do k = 1, 2
    i = search(targets(k))
    if (i > 0) then
      write(*, '(a, i0, a, i0)') 'Found ', targets(k), ' at index ', i - 1
    else
      write(*, '(i0, a)') targets(k), ' not found'
    end if
  end do

contains
  integer function search(target)
    integer, intent(in) :: target
    integer :: lo, hi, mid
    lo = 1
    hi = size(arr)
    search = 0
    do while (lo <= hi)
      mid = (lo + hi) / 2
      if (arr(mid) == target) then
        search = mid
        return
      else if (arr(mid) < target) then
        lo = mid + 1
      else
        hi = mid - 1
      end if
    end do
  end function search
end program binary_search
