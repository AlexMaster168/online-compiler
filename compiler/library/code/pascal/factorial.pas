{ Факториал рекурсией. 20! — предел Int64. }
program Factorial;

{$mode objfpc}

function Fact(n: Integer): Int64;
begin
  if n <= 1 then
    Result := 1
  else
    Result := n * Fact(n - 1);
end;

begin
  WriteLn('10! = ', Fact(10));
  WriteLn('20! = ', Fact(20));
end.
