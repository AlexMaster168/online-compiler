--  Дейкстра за O(V^2) на матрице весов (0 — нет ребра).
with Ada.Text_IO; use Ada.Text_IO;

procedure Main is
   subtype Vertex is Natural range 0 .. 4;
   W : constant array (Vertex, Vertex) of Natural :=
     ((0, 4, 1, 0, 0),
      (0, 0, 0, 1, 0),
      (0, 2, 0, 5, 0),
      (0, 0, 0, 0, 3),
      (0, 0, 0, 0, 0));
   Inf  : constant Natural := Natural'Last;
   Dist : array (Vertex) of Natural := (0 => 0, others => Inf);
   Done : array (Vertex) of Boolean := (others => False);
   Best : Integer;
begin
   for Step in Vertex loop
      Best := -1;
      for I in Vertex loop
         if not Done (I) and then (Best = -1 or else Dist (I) < Dist (Best)) then
            Best := I;
         end if;
      end loop;
      exit when Dist (Best) = Inf;
      Done (Best) := True;
      for U in Vertex loop
         if W (Best, U) > 0 and then Dist (Best) + W (Best, U) < Dist (U) then
            Dist (U) := Dist (Best) + W (Best, U);
         end if;
      end loop;
   end loop;
   Put ("Dijkstra from 0:");
   for D of Dist loop
      Put (Natural'Image (D));
   end loop;
   New_Line;
end Main;
