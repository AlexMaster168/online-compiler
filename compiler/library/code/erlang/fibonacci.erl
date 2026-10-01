%% Числа Фибоначчи хвостовой рекурсией с аккумуляторами. Целые в Erlang безразмерные.
-module(main).
-export([main/0]).

fib(N) -> fib(N, 0, 1).
fib(0, A, _) -> A;
fib(N, A, B) -> fib(N - 1, B, A + B).

main() ->
    First = [integer_to_list(fib(I)) || I <- lists:seq(0, 14)],
    io:format("Fibonacci: ~s~n", [lists:join(" ", First)]),
    io:format("F(50) = ~p~n", [fib(50)]).
