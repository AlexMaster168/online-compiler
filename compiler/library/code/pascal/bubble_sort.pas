{ Сортировка пузырьком: O(n^2). Если за проход не было обменов — массив уже отсортирован. }
program BubbleSort;

{$mode objfpc}

var
  a: array[0..5] of Integer = (5, 2, 9, 1, 5, 6);
  i, j, t: Integer;
  swapped: Boolean;

begin
  for i := 0 to High(a) - 1 do
  begin
    swapped := False;
    for j := 0 to High(a) - 1 - i do
      if a[j] > a[j + 1] then
      begin
        t := a[j];
        a[j] := a[j + 1];
        a[j + 1] := t;
        swapped := True;
      end;
    if not swapped then
      Break;
  end;
  Write('Sorted:');
  for i := 0 to High(a) do
    Write(' ', a[i]);
  WriteLn;
end.
