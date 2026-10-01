{ Сортировка слиянием: всегда O(n log n), стабильная. Буфер tmp — общий для всех уровней рекурсии. }
program MergeSort;

{$mode objfpc}

type
  TIntArray = array of Integer;

var
  a, tmp: TIntArray;
  x: Integer;

procedure Sort(lo, hi: Integer);  { сортирует полуинтервал [lo, hi) }
var
  mid, i, j, k: Integer;
begin
  if hi - lo < 2 then
    Exit;
  mid := (lo + hi) div 2;
  Sort(lo, mid);
  Sort(mid, hi);
  i := lo;
  j := mid;
  k := lo;
  while (i < mid) and (j < hi) do
  begin
    if a[i] <= a[j] then
    begin
      tmp[k] := a[i];
      Inc(i);
    end
    else
    begin
      tmp[k] := a[j];
      Inc(j);
    end;
    Inc(k);
  end;
  while i < mid do begin tmp[k] := a[i]; Inc(i); Inc(k); end;
  while j < hi do begin tmp[k] := a[j]; Inc(j); Inc(k); end;
  for k := lo to hi - 1 do
    a[k] := tmp[k];
end;

begin
  a := [38, 27, 43, 3, 9, 82, 10];
  SetLength(tmp, Length(a));
  Sort(0, Length(a));
  Write('Sorted:');
  for x in a do
    Write(' ', x);
  WriteLn;
end.
