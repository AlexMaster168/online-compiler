%% Сортировка пузырьком: данные неизменяемые — каждый проход строит новый список.
-module(main).
-export([main/0]).

bubble_sort(List) ->
    case pass(List) of
        {Sorted, false} -> Sorted;
        {Next, true} -> bubble_sort(Next)
    end.

pass([A, B | Rest]) when A > B ->
    {Tail, _} = pass([A | Rest]),
    {[B | Tail], true};
pass([A | Rest]) ->
    {Tail, Swapped} = pass(Rest),
    {[A | Tail], Swapped};
pass([]) ->
    {[], false}.

join(Numbers) -> lists:join(" ", [integer_to_list(N) || N <- Numbers]).

main() ->
    io:format("Sorted: ~s~n", [join(bubble_sort([5, 2, 9, 1, 5, 6]))]).
