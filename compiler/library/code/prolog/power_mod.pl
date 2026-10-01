% Быстрое возведение в степень: чётный показатель — квадрат половины, нечётный — домножаем.
:- initialization(main, main).

power_mod(_, 0, _, 1) :- !.
power_mod(Base, Exp, M, R) :-
    Exp mod 2 =:= 0, !,
    Half is Exp // 2,
    power_mod(Base, Half, M, H),
    R is H * H mod M.
power_mod(Base, Exp, M, R) :-
    Exp1 is Exp - 1,
    power_mod(Base, Exp1, M, R1),
    R is Base * R1 mod M.

main :-
    M = 1000000007,
    power_mod(2, 30, M, A),
    power_mod(3, 200, M, B),
    format("2^30 mod ~w = ~w~n", [M, A]),
    format("3^200 mod ~w = ~w~n", [M, B]).
