--  Решето Эратосфена: O(n log log n).
with Ada.Text_IO; use Ada.Text_IO;

procedure Main is
   N : constant := 50;
   Composite : array (2 .. N) of Boolean := (others => False);
   K : Natural;
begin
   Put ("Primes up to 50:");
   for P in Composite'Range loop
      if not Composite (P) then
         Put (Integer'Image (P));
         K := P * P;
         while K <= N loop
            Composite (K) := True;
            K := K + P;
         end loop;
      end if;
   end loop;
   New_Line;
end Main;
