! Сортировка пузырьком: O(n^2). Массивы в Fortran по умолчанию индексируются с 1.
program bubble_sort
  implicit none
  integer :: a(6) = [5, 2, 9, 1, 5, 6]
  integer :: i, j, t
  logical :: swapped

  do i = 1, size(a) - 1
    swapped = .false.
    do j = 1, size(a) - i
      if (a(j) > a(j + 1)) then
        t = a(j)
        a(j) = a(j + 1)
        a(j + 1) = t
        swapped = .true.
      end if
    end do
    if (.not. swapped) exit
  end do
  write(*, '(a, *(1x, i0))') 'Sorted:', a
end program bubble_sort
