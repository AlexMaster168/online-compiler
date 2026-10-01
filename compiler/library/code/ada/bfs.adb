--  Поиск в ширину: очередь на массиве, O(V + E).
with Ada.Text_IO; use Ada.Text_IO;

procedure Main is
   subtype Vertex is Natural range 0 .. 5;
   type Neighbours is array (1 .. 2) of Vertex;
   Graph : constant array (Vertex) of Neighbours :=
     ((1, 2), (0, 3), (0, 4), (1, 5), (2, 5), (3, 4));
   Dist  : array (Vertex) of Integer := (others => -1);
   Queue : array (1 .. 6) of Vertex;
   Head, Tail : Natural := 1;
   V : Vertex;
begin
   Dist (0) := 0;
   Queue (1) := 0;
   Put ("BFS order:");
   while Head <= Tail loop
      V := Queue (Head);
      Head := Head + 1;
      Put (Integer'Image (V));
      for U of Graph (V) loop
         if Dist (U) = -1 then
            Dist (U) := Dist (V) + 1;
            Tail := Tail + 1;
            Queue (Tail) := U;
         end if;
      end loop;
   end loop;
   New_Line;
   Put ("Distances:");
   for D of Dist loop
      Put (Integer'Image (D));
   end loop;
   New_Line;
end Main;
