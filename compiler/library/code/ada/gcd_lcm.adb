--  НОД по Евклиду: gcd(a, b) = gcd(b, a mod b). НОК = a / gcd * b.
with Ada.Text_IO; use Ada.Text_IO;

procedure Main is
   function Gcd (A, B : Natural) return Natural is
     (if B = 0 then A else Gcd (B, A mod B));  --  выражение-функция, Ada 2012

   function Lcm (A, B : Natural) return Natural is (A / Gcd (A, B) * B);
begin
   Put_Line ("GCD(48, 18) =" & Natural'Image (Gcd (48, 18)));
   Put_Line ("LCM(48, 18) =" & Natural'Image (Lcm (48, 18)));
end Main;
