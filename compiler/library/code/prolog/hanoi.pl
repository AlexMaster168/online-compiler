% Ханойские башни: hanoi/5 возвращает число ходов, печатая сами ходы по пути.
:- initialization(main, main).

hanoi(0, _, _, _, 0) :- !.
hanoi(N, From, Spare, To, Moves) :-
    N1 is N - 1,
    hanoi(N1, From, To, Spare, M1),
    format("Move disk ~w from ~w to ~w~n", [N, From, To]),
    hanoi(N1, Spare, From, To, M2),
    Moves is M1 + 1 + M2.

main :-
    hanoi(3, 'A', 'B', 'C', Moves),
    format("Total moves: ~w~n", [Moves]).
