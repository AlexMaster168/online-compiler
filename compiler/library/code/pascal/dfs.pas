{ Поиск в глубину рекурсией: O(V + E). }
program Dfs;

const
  V = 6;
  Adj: array[0..V - 1, 0..1] of Integer = ((1, 2), (0, 3), (0, 4), (1, 5), (2, 5), (3, 4));

var
  visited: array[0..V - 1] of Boolean;

procedure Visit(u: Integer);
var
  k: Integer;
begin
  visited[u] := True;
  Write(' ', u);
  for k := 0 to 1 do
    if not visited[Adj[u, k]] then
      Visit(Adj[u, k]);
end;

begin
  FillChar(visited, SizeOf(visited), False);
  Write('DFS order:');
  Visit(0);
  WriteLn;
end.
