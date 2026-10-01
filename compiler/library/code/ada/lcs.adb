--  Наибольшая общая подпоследовательность: dp (I, J) — длина LCS для префиксов. O(n * m).
with Ada.Text_IO; use Ada.Text_IO;

procedure Main is
   function Lcs (A, B : String) return Natural is
      Dp : array (0 .. A'Length, 0 .. B'Length) of Natural := (others => (others => 0));
   begin
      for I in 1 .. A'Length loop
         for J in 1 .. B'Length loop
            if A (A'First + I - 1) = B (B'First + J - 1) then
               Dp (I, J) := Dp (I - 1, J - 1) + 1;
            else
               Dp (I, J) := Natural'Max (Dp (I - 1, J), Dp (I, J - 1));
            end if;
         end loop;
      end loop;
      return Dp (A'Length, B'Length);
   end Lcs;
begin
   Put_Line ("LCS(ABCBDAB, BDCABA) =" & Natural'Image (Lcs ("ABCBDAB", "BDCABA")));
end Main;
