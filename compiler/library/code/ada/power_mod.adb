--  Быстрое возведение в степень: O(log n).
with Ada.Text_IO; use Ada.Text_IO;

procedure Main is
   subtype Big is Long_Long_Integer;
   M : constant Big := 1_000_000_007;

   function Pow_Mod (Base, Exp : Big) return Big is
      Result : Big := 1;
      B : Big := Base mod M;
      E : Big := Exp;
   begin
      while E > 0 loop
         if E mod 2 = 1 then
            Result := Result * B mod M;
         end if;
         B := B * B mod M;
         E := E / 2;
      end loop;
      return Result;
   end Pow_Mod;
begin
   Put_Line ("2^30 mod" & Big'Image (M) & " =" & Big'Image (Pow_Mod (2, 30)));
   Put_Line ("3^200 mod" & Big'Image (M) & " =" & Big'Image (Pow_Mod (3, 200)));
end Main;
