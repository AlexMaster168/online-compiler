% НОД по Евклиду: два правила — база (B = 0) и шаг. (В SWI есть встроенная gcd/2 — пишем свою.)
:- initialization(main, main).

my_gcd(A, 0, A) :- !.
my_gcd(A, B, G) :- R is A mod B, my_gcd(B, R, G).

my_lcm(A, B, L) :- my_gcd(A, B, G), L is A // G * B.

main :-
    my_gcd(48, 18, G),
    my_lcm(48, 18, L),
    format("GCD(48, 18) = ~w~n", [G]),
    format("LCM(48, 18) = ~w~n", [L]).
