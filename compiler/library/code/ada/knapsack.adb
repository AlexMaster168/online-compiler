--  Рюкзак 0/1: Dp (C) — лучшая ценность при вместимости C; C идёт сверху вниз (reverse).
with Ada.Text_IO; use Ada.Text_IO;

procedure Main is
   Capacity : constant := 7;
   type Item is record
      Weight, Value : Natural;
   end record;
   Items : constant array (1 .. 4) of Item := ((1, 1), (3, 4), (4, 5), (5, 7));
   Dp : array (0 .. Capacity) of Natural := (others => 0);
begin
   for It of Items loop
      for C in reverse It.Weight .. Capacity loop
         Dp (C) := Natural'Max (Dp (C), Dp (C - It.Weight) + It.Value);
      end loop;
   end loop;
   Put_Line ("Knapsack max value:" & Natural'Image (Dp (Capacity)));
end Main;
