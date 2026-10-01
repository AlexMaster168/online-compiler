! Факториал рекурсией. 20! — предел integer(int64).
program factorial_demo
  use iso_fortran_env, only: int64
  implicit none
  write(*, '(a, i0)') '10! = ', factorial(10)
  write(*, '(a, i0)') '20! = ', factorial(20)

contains
  recursive integer(int64) function factorial(n) result(r)
    integer, intent(in) :: n
    if (n <= 1) then
      r = 1
    else
      r = n * factorial(n - 1)
    end if
  end function factorial
end program factorial_demo
