%% Решето Эратосфена на списках: голова — простое, из хвоста убираем её кратные.
-module(main).
-export([main/0]).

sieve([]) -> [];
sieve([P | Rest]) -> [P | sieve([X || X <- Rest, X rem P =/= 0])].

main() ->
    Primes = sieve(lists:seq(2, 50)),
    io:format("Primes up to 50: ~s~n", [lists:join(" ", [integer_to_list(P) || P <- Primes])]).
