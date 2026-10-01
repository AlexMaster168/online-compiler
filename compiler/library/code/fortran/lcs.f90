! Наибольшая общая подпоследовательность: dp(i, j) — длина LCS для префиксов. O(n * m).
program lcs
  implicit none
  character(len=*), parameter :: a = 'ABCBDAB', b = 'BDCABA'
  integer :: dp(0:len(a), 0:len(b)), i, j

  dp = 0
  do i = 1, len(a)
    do j = 1, len(b)
      if (a(i:i) == b(j:j)) then
        dp(i, j) = dp(i - 1, j - 1) + 1
      else
        dp(i, j) = max(dp(i - 1, j), dp(i, j - 1))
      end if
    end do
  end do
  write(*, '(a, i0)') 'LCS(ABCBDAB, BDCABA) = ', dp(len(a), len(b))
end program lcs
