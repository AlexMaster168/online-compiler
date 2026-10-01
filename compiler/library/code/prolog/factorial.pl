% Факториал рекурсией: два предложения — база и шаг.
:- initialization(main, main).

factorial(0, 1) :- !.
factorial(N, F) :- N1 is N - 1, factorial(N1, F1), F is N * F1.

main :-
    factorial(10, F10),
    factorial(20, F20),
    format("10! = ~w~n", [F10]),
    format("20! = ~w~n", [F20]).
