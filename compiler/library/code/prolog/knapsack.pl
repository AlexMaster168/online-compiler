% Рюкзак 0/1: для каждого предмета — максимум из «не брать» и «взять». Табличная мемоизация (table).
:- initialization(main, main).
:- table best/3.

items([1-1, 3-4, 4-5, 5-7]).        % вес-ценность

best([], _, 0).
best([W-V | Rest], Cap, Best) :-
    best(Rest, Cap, Skip),
    (   W =< Cap
    ->  Cap1 is Cap - W, best(Rest, Cap1, Take0), Take is Take0 + V, Best is max(Skip, Take)
    ;   Best = Skip
    ).

main :-
    items(Items),
    best(Items, 7, Best),
    format("Knapsack max value: ~w~n", [Best]).
