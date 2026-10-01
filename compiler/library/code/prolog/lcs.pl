% Наибольшая общая подпоследовательность: :- table включает мемоизацию,
% поэтому прямая рекурсивная формула работает за O(n * m), а не экспоненциально.
:- initialization(main, main).
:- table lcs/3.

lcs([], _, 0) :- !.
lcs(_, [], 0) :- !.
lcs([X | Xs], [X | Ys], L) :- !, lcs(Xs, Ys, L0), L is L0 + 1.
lcs([X | Xs], [Y | Ys], L) :-
    lcs(Xs, [Y | Ys], L1),
    lcs([X | Xs], Ys, L2),
    L is max(L1, L2).

main :-
    string_chars("ABCBDAB", A),
    string_chars("BDCABA", B),
    lcs(A, B, L),
    format("LCS(ABCBDAB, BDCABA) = ~w~n", [L]).
