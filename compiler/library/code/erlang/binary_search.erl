%% Бинарный поиск по кортежу: element/2 даёт доступ по индексу за O(1) (у списков — O(n)).
-module(main).
-export([main/0]).

binary_search(Tuple, Target) -> search(Tuple, Target, 1, tuple_size(Tuple)).

search(_Tuple, _Target, Lo, Hi) when Lo > Hi -> not_found;
search(Tuple, Target, Lo, Hi) ->
    Mid = (Lo + Hi) div 2,
    case element(Mid, Tuple) of
        Target -> {found, Mid - 1};                 % индексы с нуля, как в других языках
        Value when Value < Target -> search(Tuple, Target, Mid + 1, Hi);
        _ -> search(Tuple, Target, Lo, Mid - 1)
    end.

main() ->
    Arr = {1, 3, 5, 7, 9, 11, 13, 15, 17, 19},
    lists:foreach(
        fun(Target) ->
            case binary_search(Arr, Target) of
                {found, I} -> io:format("Found ~p at index ~p~n", [Target, I]);
                not_found -> io:format("~p not found~n", [Target])
            end
        end,
        [7, 4]).
