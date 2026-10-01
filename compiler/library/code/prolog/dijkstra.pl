% Дейкстра за O(V^2): Pending — необработанные вершины, Dist — пары V-D (inf — недостижима).
:- initialization(main, main).

edge(0, 1, 4). edge(0, 2, 1). edge(2, 1, 2). edge(1, 3, 1). edge(2, 3, 5). edge(3, 4, 3).

dijkstra(Pending, Dist, Dist) :-
    \+ (member(V, Pending), memberchk(V-D, Dist), D \== inf), !.
dijkstra(Pending, Dist0, Dist) :-
    findall(D-V, (member(V, Pending), memberchk(V-D, Dist0), D \== inf), Candidates),
    min_member(Dv-V, Candidates),
    selectchk(V, Pending, Rest),
    foldl(relax(V, Dv), [0, 1, 2, 3, 4], Dist0, Dist1),
    dijkstra(Rest, Dist1, Dist).

relax(V, Dv, U, Dist0, Dist) :-
    (   edge(V, U, W),
        Nd is Dv + W,
        memberchk(U-Du, Dist0),
        (Du == inf ; Nd < Du)
    ->  selectchk(U-Du, Dist0, U-Nd, Dist)
    ;   Dist = Dist0
    ).

main :-
    Init = [0-0, 1-inf, 2-inf, 3-inf, 4-inf],
    dijkstra([0, 1, 2, 3, 4], Init, Dist),
    pairs_values(Dist, Values),
    atomic_list_concat(Values, ' ', Text),
    format("Dijkstra from 0: ~w~n", [Text]).
