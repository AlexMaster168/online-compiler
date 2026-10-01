% Бинарный поиск: отрезок [Lo, Hi] сужаем вдвое. Массив — терм arr(...), arg/3 даёт доступ за O(1).
:- initialization(main, main).

binary_search(Arr, Target, Index) :-
    functor(Arr, _, N),
    search(Arr, Target, 1, N, Index).

search(Arr, Target, Lo, Hi, Index) :-
    Lo =< Hi,
    Mid is (Lo + Hi) // 2,
    arg(Mid, Arr, Value),
    (   Value =:= Target -> Index is Mid - 1          % индексы с нуля, как в других языках
    ;   Value < Target -> Lo1 is Mid + 1, search(Arr, Target, Lo1, Hi, Index)
    ;   Hi1 is Mid - 1, search(Arr, Target, Lo, Hi1, Index)
    ).

report(Arr, Target) :-
    (   binary_search(Arr, Target, I)
    ->  format("Found ~w at index ~w~n", [Target, I])
    ;   format("~w not found~n", [Target])
    ).

main :-
    Arr = arr(1, 3, 5, 7, 9, 11, 13, 15, 17, 19),
    report(Arr, 7),
    report(Arr, 4).
