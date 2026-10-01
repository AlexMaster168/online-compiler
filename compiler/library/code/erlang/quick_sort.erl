%% Быстрая сортировка: опора — голова списка, генераторы списков отбирают меньшие и остальные.
-module(main).
-export([main/0]).

quick_sort([]) -> [];
quick_sort([Pivot | Rest]) ->
    quick_sort([X || X <- Rest, X < Pivot]) ++ [Pivot] ++ quick_sort([X || X <- Rest, X >= Pivot]).

main() ->
    Sorted = quick_sort([10, 7, 8, 9, 1, 5, 3]),
    io:format("Sorted: ~s~n", [lists:join(" ", [integer_to_list(N) || N <- Sorted])]).
