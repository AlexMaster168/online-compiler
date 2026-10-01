% Поиск в глубину: свёртка foldl по соседям протягивает список посещённых вершин.
:- initialization(main, main).

edge(0, 1). edge(0, 2). edge(1, 3). edge(2, 4). edge(3, 5). edge(4, 5).
neighbours(V, Us) :- findall(U, (edge(V, U) ; edge(U, V)), Us0), sort(Us0, Us).

dfs(V, Visited, Visited) :- memberchk(V, Visited), !.
dfs(V, Visited0, Visited) :-
    neighbours(V, Us),
    foldl(dfs, Us, [V | Visited0], Visited).

main :-
    dfs(0, [], Reversed),
    reverse(Reversed, Order),
    atomic_list_concat(Order, ' ', Text),
    format("DFS order: ~w~n", [Text]).
