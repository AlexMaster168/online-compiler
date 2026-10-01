--  Ханойские башни: 2^n - 1 ходов.
with Ada.Text_IO; use Ada.Text_IO;

procedure Main is
   Moves : Natural := 0;

   procedure Hanoi (N : Natural; Source, Spare, Target : Character) is
   begin
      if N = 0 then
         return;
      end if;
      Hanoi (N - 1, Source, Target, Spare);
      Put_Line ("Move disk" & Natural'Image (N) & " from " & Source & " to " & Target);
      Moves := Moves + 1;
      Hanoi (N - 1, Spare, Source, Target);
   end Hanoi;
begin
   Hanoi (3, 'A', 'B', 'C');
   Put_Line ("Total moves:" & Natural'Image (Moves));
end Main;
