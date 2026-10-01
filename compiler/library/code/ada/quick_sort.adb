--  Быстрая сортировка (разбиение Ломуто): in out — параметр передаётся по ссылке.
with Ada.Text_IO; use Ada.Text_IO;

procedure Main is
   type Int_Array is array (Natural range <>) of Integer;

   procedure Swap (X, Y : in out Integer) is
      T : constant Integer := X;
   begin
      X := Y;
      Y := T;
   end Swap;

   procedure Sort (A : in out Int_Array; Lo, Hi : Integer) is
      Pivot : Integer;
      I : Integer;
   begin
      if Lo >= Hi then
         return;
      end if;
      Pivot := A (Hi);
      I := Lo;
      for J in Lo .. Hi - 1 loop
         if A (J) < Pivot then
            Swap (A (I), A (J));
            I := I + 1;
         end if;
      end loop;
      Swap (A (I), A (Hi));
      Sort (A, Lo, I - 1);
      Sort (A, I + 1, Hi);
   end Sort;

   A : Int_Array := (10, 7, 8, 9, 1, 5, 3);
begin
   Sort (A, A'First, A'Last);
   Put ("Sorted:");
   for X of A loop
      Put (Integer'Image (X));
   end loop;
   New_Line;
end Main;
