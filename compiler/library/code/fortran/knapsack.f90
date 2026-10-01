! Рюкзак 0/1: dp(c) — лучшая ценность при вместимости c; c идёт сверху вниз.
program knapsack
  implicit none
  integer, parameter :: capacity = 7
  integer :: weights(4) = [1, 3, 4, 5], values(4) = [1, 4, 5, 7]
  integer :: dp(0:capacity), i, c

  dp = 0
  do i = 1, size(weights)
    do c = capacity, weights(i), -1
      dp(c) = max(dp(c), dp(c - weights(i)) + values(i))
    end do
  end do
  write(*, '(a, i0)') 'Knapsack max value: ', dp(capacity)
end program knapsack
