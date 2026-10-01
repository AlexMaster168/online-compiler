{ Быстрая сортировка (разбиение Ломуто): var-параметр передаёт массив по ссылке. }
program QuickSort;

{$mode objfpc}

type
  TIntArray = array of Integer;

procedure Swap(var x, y: Integer);
var
  t: Integer;
begin
  t := x;
  x := y;
  y := t;
end;

function Partition(var a: TIntArray; lo, hi: Integer): Integer;
var
  pivot, i, j: Integer;
begin
  pivot := a[hi];
  i := lo;
  for j := lo to hi - 1 do
    if a[j] < pivot then
    begin
      Swap(a[i], a[j]);
      Inc(i);
    end;
  Swap(a[i], a[hi]);
  Result := i;
end;

procedure Sort(var a: TIntArray; lo, hi: Integer);
var
  p: Integer;
begin
  if lo >= hi then
    Exit;
  p := Partition(a, lo, hi);
  Sort(a, lo, p - 1);
  Sort(a, p + 1, hi);
end;

var
  a: TIntArray;
  x: Integer;
begin
  a := [10, 7, 8, 9, 1, 5, 3];
  Sort(a, 0, High(a));
  Write('Sorted:');
  for x in a do
    Write(' ', x);
  WriteLn;
end.
