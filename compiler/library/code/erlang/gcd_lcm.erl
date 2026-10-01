%% НОД по Евклиду: две клаузы функции вместо if.
-module(main).
-export([main/0]).

gcd(A, 0) -> A;
gcd(A, B) -> gcd(B, A rem B).

lcm(A, B) -> A div gcd(A, B) * B.

main() ->
    io:format("GCD(48, 18) = ~p~n", [gcd(48, 18)]),
    io:format("LCM(48, 18) = ~p~n", [lcm(48, 18)]).
