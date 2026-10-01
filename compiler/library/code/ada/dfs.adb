--  Поиск в глубину рекурсией: O(V + E).
with Ada.Text_IO; use Ada.Text_IO;

procedure Main is
   subtype Vertex is Natural range 0 .. 5;
   type Neighbours is array (1 .. 2) of Vertex;
   Graph : constant array (Vertex) of Neighbours :=
     ((1, 2), (0, 3), (0, 4), (1, 5), (2, 5), (3, 4));
   Visited : array (Vertex) of Boolean := (others => False);

   procedure Dfs (V : Vertex) is
   begin
      Visited (V) := True;
      Put (Integer'Image (V));
      for U of Graph (V) loop
         if not Visited (U) then
            Dfs (U);
         end if;
      end loop;
   end Dfs;
begin
   Put ("DFS order:");
   Dfs (0);
   New_Line;
end Main;
