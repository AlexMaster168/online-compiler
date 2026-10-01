--  Сортировка пузырьком: O(n^2). Если за проход не было обменов — массив уже отсортирован.
with Ada.Text_IO; use Ada.Text_IO;

procedure Main is
   type Int_Array is array (Positive range <>) of Integer;
   A : Int_Array := (5, 2, 9, 1, 5, 6);
   Swapped : Boolean;
   Tmp : Integer;
begin
   for I in A'First .. A'Last - 1 loop
      Swapped := False;
      for J in A'First .. A'Last - I loop
         if A (J) > A (J + 1) then
            Tmp := A (J);
            A (J) := A (J + 1);
            A (J + 1) := Tmp;
            Swapped := True;
         end if;
      end loop;
      exit when not Swapped;
   end loop;
   Put ("Sorted:");
   for X of A loop
      Put (Integer'Image (X));  --  'Image добавляет пробел перед положительным числом
   end loop;
   New_Line;
end Main;
