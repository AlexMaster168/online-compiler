%% Наибольшая общая подпоследовательность: строим таблицу построчно, храним только предыдущую строку.
-module(main).
-export([main/0]).

lcs(A, B) ->
    First = lists:duplicate(length(B) + 1, 0),
    lists:last(lists:foldl(fun(X, Prev) -> next_row(X, B, Prev) end, First, A)).

next_row(X, B, Prev) ->
    {Row, _} = lists:foldl(
        fun({Y, Diag, Up}, {Acc, Left}) ->
            Value = case X =:= Y of
                true -> Diag + 1;
                false -> max(Up, Left)
            end,
            {[Value | Acc], Value}
        end,
        {[0], 0}, lists:zip3(B, lists:droplast(Prev), tl(Prev))),
    lists:reverse(Row).

main() ->
    io:format("LCS(ABCBDAB, BDCABA) = ~p~n", [lcs("ABCBDAB", "BDCABA")]).
