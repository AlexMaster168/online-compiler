! НОД по Евклиду: gcd(a, b) = gcd(b, mod(a, b)). Рекурсивная функция требует слова recursive.
program gcd_lcm
  implicit none
  write(*, '(a, i0)') 'GCD(48, 18) = ', gcd(48, 18)
  write(*, '(a, i0)') 'LCM(48, 18) = ', lcm(48, 18)

contains
  recursive integer function gcd(a, b) result(r)
    integer, intent(in) :: a, b
    if (b == 0) then
      r = a
    else
      r = gcd(b, mod(a, b))
    end if
  end function gcd

  integer function lcm(a, b)
    integer, intent(in) :: a, b
    lcm = a / gcd(a, b) * b
  end function lcm
end program gcd_lcm
