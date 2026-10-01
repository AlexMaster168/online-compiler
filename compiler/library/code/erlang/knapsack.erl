%% Рюкзак 0/1: для каждого предмета строим новую строку dp (кортеж — быстрый доступ по индексу).
-module(main).
-export([main/0]).

knapsack(Items, Capacity) ->
    Init = list_to_tuple(lists:duplicate(Capacity + 1, 0)),
    Dp = lists:foldl(
        fun({W, V}, Row) ->
            list_to_tuple([best(Row, C, W, V) || C <- lists:seq(0, Capacity)])
        end,
        Init, Items),
    element(Capacity + 1, Dp).

best(Row, C, W, V) when C >= W -> max(element(C + 1, Row), element(C - W + 1, Row) + V);
best(Row, C, _W, _V) -> element(C + 1, Row).

main() ->
    io:format("Knapsack max value: ~p~n", [knapsack([{1, 1}, {3, 4}, {4, 5}, {5, 7}], 7)]).
