{ НОД по Евклиду: gcd(a, b) = gcd(b, a mod b). НОК = a div gcd * b. }
program GcdLcm;

{$mode objfpc}

function Gcd(a, b: Int64): Int64;
begin
  if b = 0 then
    Result := a
  else
    Result := Gcd(b, a mod b);
end;

function Lcm(a, b: Int64): Int64;
begin
  Result := a div Gcd(a, b) * b;
end;

begin
  WriteLn('GCD(48, 18) = ', Gcd(48, 18));
  WriteLn('LCM(48, 18) = ', Lcm(48, 18));
end.
