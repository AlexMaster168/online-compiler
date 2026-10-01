{ Дейкстра за O(V^2) на матрице весов (0 — нет ребра). }
program Dijkstra;

const
  V = 5;
  Inf = High(Integer);
  W: array[0..V - 1, 0..V - 1] of Integer = (
    (0, 4, 1, 0, 0),
    (0, 0, 0, 1, 0),
    (0, 2, 0, 5, 0),
    (0, 0, 0, 0, 3),
    (0, 0, 0, 0, 0));

var
  dist: array[0..V - 1] of Integer;
  done: array[0..V - 1] of Boolean;
  step, i, u, best: Integer;

begin
  for i := 0 to V - 1 do
  begin
    dist[i] := Inf;
    done[i] := False;
  end;
  dist[0] := 0;
  for step := 1 to V do
  begin
    best := -1;
    for i := 0 to V - 1 do
      if not done[i] and ((best = -1) or (dist[i] < dist[best])) then
        best := i;
    if dist[best] = Inf then
      Break;
    done[best] := True;
    for u := 0 to V - 1 do
      if (W[best, u] > 0) and (dist[best] + W[best, u] < dist[u]) then
        dist[u] := dist[best] + W[best, u];
  end;
  Write('Dijkstra from 0:');
  for i := 0 to V - 1 do
    Write(' ', dist[i]);
  WriteLn;
end.
