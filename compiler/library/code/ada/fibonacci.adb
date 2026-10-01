--  Числа Фибоначчи итеративно. F(50) не влезает в Integer — Long_Long_Integer (64 бита).
with Ada.Text_IO; use Ada.Text_IO;

procedure Main is
   subtype Big is Long_Long_Integer;

   function Fib (N : Natural) return Big is
      A : Big := 0;
      B : Big := 1;
      T : Big;
   begin
      for I in 1 .. N loop
         T := A + B;
         A := B;
         B := T;
      end loop;
      return A;
   end Fib;
begin
   Put ("Fibonacci:");
   for I in 0 .. 14 loop
      Put (Big'Image (Fib (I)));
   end loop;
   New_Line;
   Put_Line ("F(50) =" & Big'Image (Fib (50)));
end Main;
