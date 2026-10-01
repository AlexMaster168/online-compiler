--  Бинарный поиск: O(log n). Индексы массива объявлены с 0 — так печать совпадает с другими языками.
with Ada.Text_IO; use Ada.Text_IO;

procedure Main is
   type Int_Array is array (Natural range <>) of Integer;
   Arr : constant Int_Array := (1, 3, 5, 7, 9, 11, 13, 15, 17, 19);

   function Search (Target : Integer) return Integer is
      Lo  : Integer := Arr'First;
      Hi  : Integer := Arr'Last;
      Mid : Integer;
   begin
      while Lo <= Hi loop
         Mid := (Lo + Hi) / 2;
         if Arr (Mid) = Target then
            return Mid;
         elsif Arr (Mid) < Target then
            Lo := Mid + 1;
         else
            Hi := Mid - 1;
         end if;
      end loop;
      return -1;
   end Search;

   I : Integer;
begin
   for Target of Int_Array'(7, 4) loop
      I := Search (Target);
      if I >= 0 then
         Put_Line ("Found" & Integer'Image (Target) & " at index" & Integer'Image (I));
      else
         Put_Line (Integer'Image (Target) (2 .. Integer'Image (Target)'Last) & " not found");
      end if;
   end loop;
end Main;
