! Быстрое возведение в степень: O(log n). Произведение < 2^63 — integer(int64) хватает.
program power_mod
  use iso_fortran_env, only: int64
  implicit none
  integer(int64), parameter :: m = 1000000007_int64

  write(*, '(a, i0, a, i0)') '2^30 mod ', m, ' = ', pow_mod(2_int64, 30_int64)
  write(*, '(a, i0, a, i0)') '3^200 mod ', m, ' = ', pow_mod(3_int64, 200_int64)

contains
  integer(int64) function pow_mod(base, exp) result(r)
    integer(int64), intent(in) :: base, exp
    integer(int64) :: b, e
    r = 1
    b = mod(base, m)
    e = exp
    do while (e > 0)
      if (btest(e, 0)) r = mod(r * b, m)
      b = mod(b * b, m)
      e = shiftr(e, 1)
    end do
  end function pow_mod
end program power_mod
