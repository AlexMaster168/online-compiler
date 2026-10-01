%% Факториал рекурсией: клауза для нуля и общая.
-module(main).
-export([main/0]).

factorial(0) -> 1;
factorial(N) when N > 0 -> N * factorial(N - 1).

main() ->
    io:format("10! = ~p~n", [factorial(10)]),
    io:format("20! = ~p~n", [factorial(20)]).
