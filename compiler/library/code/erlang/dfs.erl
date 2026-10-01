%% Поиск в глубину: lists:foldl протягивает список посещённых вершин через рекурсию.
-module(main).
-export([main/0]).

graph() -> #{0 => [1, 2], 1 => [0, 3], 2 => [0, 4], 3 => [1, 5], 4 => [2, 5], 5 => [3, 4]}.

dfs(V, Visited) ->
    case lists:member(V, Visited) of
        true -> Visited;
        false -> lists:foldl(fun dfs/2, [V | Visited], maps:get(V, graph()))
    end.

main() ->
    Order = lists:reverse(dfs(0, [])),
    io:format("DFS order: ~s~n", [lists:join(" ", [integer_to_list(V) || V <- Order])]).
