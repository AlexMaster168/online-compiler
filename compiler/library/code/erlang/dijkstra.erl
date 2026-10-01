%% Дейкстра с gb_sets как приоритетной очередью пар {расстояние, вершина}. O((V + E) log V).
-module(main).
-export([main/0]).

graph() -> #{0 => [{1, 4}, {2, 1}], 1 => [{3, 1}], 2 => [{1, 2}, {3, 5}], 3 => [{4, 3}], 4 => []}.

dijkstra(Start) -> loop(gb_sets:singleton({0, Start}), #{Start => 0}).

loop(Queue, Dist) ->
    case gb_sets:is_empty(Queue) of
        true -> Dist;
        false ->
            {{D, V}, Rest} = gb_sets:take_smallest(Queue),
            case D > maps:get(V, Dist) of
                true -> loop(Rest, Dist);                % устаревшая запись
                false ->
                    {Queue1, Dist1} = lists:foldl(
                        fun({U, W}, {Q, Ds}) ->
                            case D + W < maps:get(U, Ds, infinity) of
                                true -> {gb_sets:add({D + W, U}, Q), Ds#{U => D + W}};
                                false -> {Q, Ds}
                            end
                        end,
                        {Rest, Dist}, maps:get(V, graph())),
                    loop(Queue1, Dist1)
            end
    end.

main() ->
    Dist = dijkstra(0),
    Values = [integer_to_list(maps:get(V, Dist)) || V <- lists:seq(0, 4)],
    io:format("Dijkstra from 0: ~s~n", [lists:join(" ", Values)]).
