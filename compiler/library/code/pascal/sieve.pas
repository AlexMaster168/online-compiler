{ Решето Эратосфена: O(n log log n). }
program Sieve;

const
  N = 50;

var
  composite: array[2..N] of Boolean;
  p, k: Integer;

begin
  FillChar(composite, SizeOf(composite), False);
  Write('Primes up to ', N, ':');
  for p := 2 to N do
    if not composite[p] then
    begin
      Write(' ', p);
      k := p * p;
      while k <= N do
      begin
        composite[k] := True;
        k := k + p;
      end;
    end;
  WriteLn;
end.
