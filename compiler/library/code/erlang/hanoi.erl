%% Ханойские башни: функция возвращает число ходов, печатая их по пути.
-module(main).
-export([main/0]).

hanoi(0, _Source, _Spare, _Target) -> 0;
hanoi(N, Source, Spare, Target) ->
    Before = hanoi(N - 1, Source, Target, Spare),
    io:format("Move disk ~p from ~s to ~s~n", [N, Source, Target]),
    Before + 1 + hanoi(N - 1, Spare, Source, Target).

main() ->
    io:format("Total moves: ~p~n", [hanoi(3, "A", "B", "C")]).
