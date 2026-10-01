%% Сортировка слиянием: lists:split делит пополам, merge — несколько клауз функции.
-module(main).
-export([main/0]).

merge_sort(List) when length(List) =< 1 -> List;
merge_sort(List) ->
    {Left, Right} = lists:split(length(List) div 2, List),
    merge(merge_sort(Left), merge_sort(Right)).

merge([], Ys) -> Ys;
merge(Xs, []) -> Xs;
merge([X | Xs], [Y | _] = Ys) when X =< Y -> [X | merge(Xs, Ys)];
merge(Xs, [Y | Ys]) -> [Y | merge(Xs, Ys)].

main() ->
    Sorted = merge_sort([38, 27, 43, 3, 9, 82, 10]),
    io:format("Sorted: ~s~n", [lists:join(" ", [integer_to_list(N) || N <- Sorted])]).
