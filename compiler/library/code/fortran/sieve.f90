! Решето Эратосфена: вычёркиваем кратные срезом с шагом is_prime(p*p::p).
program sieve
  implicit none
  integer, parameter :: n = 50
  logical :: is_prime(n)
  integer :: p, i

  is_prime = .true.
  is_prime(1) = .false.
  do p = 2, int(sqrt(real(n)))
    if (is_prime(p)) is_prime(p * p::p) = .false.
  end do
  write(*, '(a, i0, a, *(1x, i0))') 'Primes up to ', n, ':', pack([(i, i = 1, n)], is_prime)
end program sieve
