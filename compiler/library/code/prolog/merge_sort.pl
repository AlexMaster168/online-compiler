% Сортировка слиянием: делим список пополам (length + append), сортируем и сливаем.
:- initialization(main, main).

merge_sort([], []) :- !.
merge_sort([X], [X]) :- !.
merge_sort(List, Sorted) :-
    length(List, N),
    Half is N // 2,
    length(Left, Half),
    append(Left, Right, List),
    merge_sort(Left, SortedLeft),
    merge_sort(Right, SortedRight),
    merge(SortedLeft, SortedRight, Sorted).

merge([], Ys, Ys) :- !.
merge(Xs, [], Xs) :- !.
merge([X | Xs], [Y | Ys], [X | Zs]) :- X =< Y, !, merge(Xs, [Y | Ys], Zs).
merge(Xs, [Y | Ys], [Y | Zs]) :- merge(Xs, Ys, Zs).

main :-
    merge_sort([38, 27, 43, 3, 9, 82, 10], Sorted),
    atomic_list_concat(Sorted, ' ', Text),
    format("Sorted: ~w~n", [Text]).
