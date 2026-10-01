% Поиск в ширину: очередь — список, расстояния — список пар V-D. Граф — факты edge/2.
:- initialization(main, main).

edge(0, 1). edge(0, 2). edge(1, 3). edge(2, 4). edge(3, 5). edge(4, 5).
neighbour(A, B) :- edge(A, B) ; edge(B, A).

bfs([], Dist, Dist, []).
bfs([V | Queue], Dist0, Dist, [V | Order]) :-
    memberchk(V-D, Dist0),
    D1 is D + 1,
    findall(U, (neighbour(V, U), \+ memberchk(U-_, Dist0)), New0),
    sort(New0, New),
    findall(U-D1, member(U, New), Pairs),
    append(Dist0, Pairs, Dist1),
    append(Queue, New, Queue1),
    bfs(Queue1, Dist1, Dist, Order).

main :-
    bfs([0], [0-0], Dist, Order),
    msort(Dist, Sorted),
    pairs_values(Sorted, Distances),
    atomic_list_concat(Order, ' ', OrderText),
    atomic_list_concat(Distances, ' ', DistText),
    format("BFS order: ~w~n", [OrderText]),
    format("Distances: ~w~n", [DistText]).
