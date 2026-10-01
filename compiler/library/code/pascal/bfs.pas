{ Поиск в ширину: очередь на массиве, O(V + E). }
program Bfs;

const
  V = 6;
  Adj: array[0..V - 1, 0..1] of Integer = ((1, 2), (0, 3), (0, 4), (1, 5), (2, 5), (3, 4));

var
  dist, queue: array[0..V - 1] of Integer;
  head, tail, i, k, u, w: Integer;

begin
  for i := 0 to V - 1 do
    dist[i] := -1;
  dist[0] := 0;
  queue[0] := 0;
  head := 0;
  tail := 1;
  Write('BFS order:');
  while head < tail do
  begin
    u := queue[head];
    Inc(head);
    Write(' ', u);
    for k := 0 to 1 do
    begin
      w := Adj[u, k];
      if dist[w] = -1 then
      begin
        dist[w] := dist[u] + 1;
        queue[tail] := w;
        Inc(tail);
      end;
    end;
  end;
  WriteLn;
  Write('Distances:');
  for i := 0 to V - 1 do
    Write(' ', dist[i]);
  WriteLn;
end.
