{ Бинарный поиск: O(log n), массив обязан быть отсортирован. }
program BinarySearch;

{$mode objfpc}

const
  Arr: array[0..9] of Integer = (1, 3, 5, 7, 9, 11, 13, 15, 17, 19);
  Targets: array[0..1] of Integer = (7, 4);

function Search(target: Integer): Integer;
var
  lo, hi, mid: Integer;
begin
  lo := 0;
  hi := High(Arr);
  while lo <= hi do
  begin
    mid := (lo + hi) div 2;
    if Arr[mid] = target then
      Exit(mid);
    if Arr[mid] < target then
      lo := mid + 1
    else
      hi := mid - 1;
  end;
  Result := -1;
end;

var
  t, i: Integer;
begin
  for t in Targets do
  begin
    i := Search(t);
    if i >= 0 then
      WriteLn('Found ', t, ' at index ', i)
    else
      WriteLn(t, ' not found');
  end;
end.
