# Решето Эратосфена на MapSet вычеркнутых чисел: свёртка по кандидатам 2..n.
defmodule Sieve do
  def primes(n) do
    {primes, _} =
      Enum.reduce(2..n, {[], MapSet.new()}, fn p, {primes, composite} ->
        if MapSet.member?(composite, p) do
          {primes, composite}
        else
          multiples = if p * p <= n, do: Enum.to_list((p * p)..n//p), else: []
          {[p | primes], MapSet.union(composite, MapSet.new(multiples))}
        end
      end)

    Enum.reverse(primes)
  end
end

IO.puts("Primes up to 50: " <> Enum.join(Sieve.primes(50), " "))
