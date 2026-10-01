{ Наибольшая общая подпоследовательность: dp[i, j] — длина LCS для префиксов. Строки в Pascal — с 1. }
program Lcs;

{$mode objfpc}

uses Math;

function LcsLength(const a, b: string): Integer;
var
  dp: array of array of Integer;
  i, j: Integer;
begin
  SetLength(dp, Length(a) + 1, Length(b) + 1);  { заполняется нулями }
  for i := 1 to Length(a) do
    for j := 1 to Length(b) do
      if a[i] = b[j] then
        dp[i, j] := dp[i - 1, j - 1] + 1
      else
        dp[i, j] := Max(dp[i - 1, j], dp[i, j - 1]);
  Result := dp[Length(a), Length(b)];
end;

begin
  WriteLn('LCS(ABCBDAB, BDCABA) = ', LcsLength('ABCBDAB', 'BDCABA'));
end.
