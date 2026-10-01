! Числа Фибоначчи итеративно. F(50) не влезает в 32 бита — integer(int64).
program fibonacci
  use iso_fortran_env, only: int64
  implicit none
  integer(int64) :: f(0:50)
  integer :: i

  f(0) = 0
  f(1) = 1
  do i = 2, 50
    f(i) = f(i - 1) + f(i - 2)
  end do
  write(*, '(a, *(1x, i0))') 'Fibonacci:', f(0:14)
  write(*, '(a, i0)') 'F(50) = ', f(50)
end program fibonacci
