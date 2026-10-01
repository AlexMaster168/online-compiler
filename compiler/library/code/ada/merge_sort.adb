--  Сортировка слиянием: функция возвращает новый массив; срезы A (A'First .. Mid) — без копирования вручную.
with Ada.Text_IO; use Ada.Text_IO;

procedure Main is
   type Int_Array is array (Positive range <>) of Integer;

   function Merge_Sort (A : Int_Array) return Int_Array is
   begin
      if A'Length <= 1 then
         return A;
      end if;
      declare
         Mid   : constant Positive := A'First + A'Length / 2 - 1;
         Left  : constant Int_Array := Merge_Sort (A (A'First .. Mid));
         Right : constant Int_Array := Merge_Sort (A (Mid + 1 .. A'Last));
         Result : Int_Array (1 .. A'Length);
         I : Positive := Left'First;
         J : Positive := Right'First;
      begin
         for K in Result'Range loop
            if J > Right'Last or else (I <= Left'Last and then Left (I) <= Right (J)) then
               Result (K) := Left (I);
               I := I + 1;
            else
               Result (K) := Right (J);
               J := J + 1;
            end if;
         end loop;
         return Result;
      end;
   end Merge_Sort;
begin
   Put ("Sorted:");
   for X of Merge_Sort ((38, 27, 43, 3, 9, 82, 10)) loop
      Put (Integer'Image (X));
   end loop;
   New_Line;
end Main;
