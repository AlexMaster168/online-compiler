{ Ханойские башни: 2^n - 1 ходов. }
program Hanoi;

var
  moves: Integer = 0;

procedure Move(n: Integer; source, spare, target: Char);
begin
  if n = 0 then
    Exit;
  Move(n - 1, source, target, spare);
  WriteLn('Move disk ', n, ' from ', source, ' to ', target);
  Inc(moves);
  Move(n - 1, spare, source, target);
end;

begin
  Move(3, 'A', 'B', 'C');
  WriteLn('Total moves: ', moves);
end.
