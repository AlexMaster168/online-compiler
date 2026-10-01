--  Факториал рекурсией. 20! — предел Long_Long_Integer; переполнение в Ada — исключение, а не мусор.
with Ada.Text_IO; use Ada.Text_IO;

procedure Main is
   function Factorial (N : Natural) return Long_Long_Integer is
     (if N <= 1 then 1 else Long_Long_Integer (N) * Factorial (N - 1));
begin
   Put_Line ("10! =" & Long_Long_Integer'Image (Factorial (10)));
   Put_Line ("20! =" & Long_Long_Integer'Image (Factorial (20)));
end Main;
