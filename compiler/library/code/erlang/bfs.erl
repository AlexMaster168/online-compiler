%% Поиск в ширину: очередь — модуль queue, расстояния — map. Состояние — аргументы рекурсии.
-module(main).
-export([main/0]).

graph() -> #{0 => [1, 2], 1 => [0, 3], 2 => [0, 4], 3 => [1, 5], 4 => [2, 5], 5 => [3, 4]}.

bfs(Start) -> loop(queue:from_list([Start]), #{Start => 0}, []).

loop(Queue, Dist, Order) ->
    case queue:out(Queue) of
        {empty, _} ->
            {lists:reverse(Order), Dist};
        {{value, V}, Rest} ->
            New = [U || U <- maps:get(V, graph()), not maps:is_key(U, Dist)],
            D = maps:get(V, Dist) + 1,
            Dist1 = lists:foldl(fun(U, Acc) -> Acc#{U => D} end, Dist, New),
            Queue1 = lists:foldl(fun queue:in/2, Rest, New),
            loop(Queue1, Dist1, [V | Order])
    end.

join(Numbers) -> lists:join(" ", [integer_to_list(N) || N <- Numbers]).

main() ->
    {Order, Dist} = bfs(0),
    io:format("BFS order: ~s~n", [join(Order)]),
    io:format("Distances: ~s~n", [join([maps:get(V, Dist) || V <- lists:seq(0, 5)])]).
