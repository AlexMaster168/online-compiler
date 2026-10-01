% Сортировка пузырьком: проход меняет соседей местами; повторяем, пока проход что-то менял.
:- initialization(main, main).

bubble_sort(List, Sorted) :-
    pass(List, Passed, Swapped),
    (   Swapped == true
    ->  bubble_sort(Passed, Sorted)
    ;   Sorted = Passed
    ).

pass([A, B | Rest], [B | Out], true) :-
    A > B, !,
    pass([A | Rest], Out, _).
pass([A | Rest], [A | Out], Swapped) :-
    Rest \== [], !,
    pass(Rest, Out, Swapped).
pass(List, List, false).

main :-
    bubble_sort([5, 2, 9, 1, 5, 6], Sorted),
    atomic_list_concat(Sorted, ' ', Text),
    format("Sorted: ~w~n", [Text]).
