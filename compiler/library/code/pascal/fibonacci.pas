{ Числа Фибоначчи итеративно. F(50) не влезает в Integer — Int64. }
program Fibonacci;

{$mode objfpc}

function Fib(n: Integer): Int64;
var
  a, b, t: Int64;
  i: Integer;
begin
  a := 0;
  b := 1;
  for i := 1 to n do
  begin
    t := a + b;
    a := b;
    b := t;
  end;
  Result := a;
end;

var
  i: Integer;
begin
  Write('Fibonacci:');
  for i := 0 to 14 do
    Write(' ', Fib(i));
  WriteLn;
  WriteLn('F(50) = ', Fib(50));
end.
