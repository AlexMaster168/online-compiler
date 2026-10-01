{ Рюкзак 0/1: dp[c] — лучшая ценность при вместимости c; c идёт сверху вниз. }
program Knapsack;

uses Math;

const
  Capacity = 7;
  Weights: array[0..3] of Integer = (1, 3, 4, 5);
  Values: array[0..3] of Integer = (1, 4, 5, 7);

var
  dp: array[0..Capacity] of Integer;
  i, c: Integer;

begin
  FillChar(dp, SizeOf(dp), 0);
  for i := 0 to High(Weights) do
    for c := Capacity downto Weights[i] do
      dp[c] := Max(dp[c], dp[c - Weights[i]] + Values[i]);
  WriteLn('Knapsack max value: ', dp[Capacity]);
end.
