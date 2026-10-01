%% Быстрое возведение в степень: band и bsr — побитовые И и сдвиг.
-module(main).
-export([main/0]).

-define(MOD, 1000000007).

power_mod(Base, Exp, M) -> power_mod(Base rem M, Exp, M, 1).

power_mod(_Base, 0, _M, Acc) -> Acc;
power_mod(Base, Exp, M, Acc) ->
    Acc1 = case Exp band 1 of
        1 -> Acc * Base rem M;
        0 -> Acc
    end,
    power_mod(Base * Base rem M, Exp bsr 1, M, Acc1).

main() ->
    io:format("2^30 mod ~p = ~p~n", [?MOD, power_mod(2, 30, ?MOD)]),
    io:format("3^200 mod ~p = ~p~n", [?MOD, power_mod(3, 200, ?MOD)]).
