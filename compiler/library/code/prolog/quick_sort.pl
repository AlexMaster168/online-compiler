% Быстрая сортировка: делим хвост на «меньше опоры» и остальное (partition/4), сортируем части.
:- initialization(main, main).

quick_sort([], []).
quick_sort([Pivot | Rest], Sorted) :-
    partition([X]>>(X < Pivot), Rest, Smaller, Larger),
    quick_sort(Smaller, SortedSmaller),
    quick_sort(Larger, SortedLarger),
    append(SortedSmaller, [Pivot | SortedLarger], Sorted).

main :-
    quick_sort([10, 7, 8, 9, 1, 5, 3], Sorted),
    atomic_list_concat(Sorted, ' ', Text),
    format("Sorted: ~w~n", [Text]).
