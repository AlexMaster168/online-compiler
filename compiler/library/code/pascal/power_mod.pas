{ Быстрое возведение в степень: O(log n). }
program PowerMod;

{$mode objfpc}

const
  M = 1000000007;

function PowMod(base, exp, modulus: Int64): Int64;
begin
  Result := 1;
  base := base mod modulus;
  while exp > 0 do
  begin
    if Odd(exp) then
      Result := Result * base mod modulus;
    base := base * base mod modulus;
    exp := exp shr 1;
  end;
end;

begin
  WriteLn('2^30 mod ', M, ' = ', PowMod(2, 30, M));
  WriteLn('3^200 mod ', M, ' = ', PowMod(3, 200, M));
end.
