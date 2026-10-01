% Числа Фибоначчи с аккумуляторами: fib(N, A, B, F) несёт пару соседних чисел. Целые безразмерные.
:- initialization(main, main).

fib(N, F) :- fib(N, 0, 1, F).
fib(0, A, _, A) :- !.
fib(N, A, B, F) :- N1 is N - 1, C is A + B, fib(N1, B, C, F).

main :-
    numlist(0, 14, Ns),
    maplist(fib, Ns, Fs),
    atomic_list_concat(Fs, ' ', Text),
    format("Fibonacci: ~w~n", [Text]),
    fib(50, F50),
    format("F(50) = ~w~n", [F50]).
