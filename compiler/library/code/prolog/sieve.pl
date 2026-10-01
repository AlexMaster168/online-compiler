% Решето Эратосфена: берём голову списка как простое и вычёркиваем её кратные из хвоста.
:- initialization(main, main).

sieve([], []).
sieve([P | Xs], [P | Primes]) :-
    exclude([X]>>(X mod P =:= 0), Xs, Rest),
    sieve(Rest, Primes).

main :-
    numlist(2, 50, Numbers),
    sieve(Numbers, Primes),
    atomic_list_concat(Primes, ' ', Text),
    format("Primes up to 50: ~w~n", [Text]).
