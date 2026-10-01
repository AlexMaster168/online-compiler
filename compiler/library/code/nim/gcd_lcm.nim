# НОД по Евклиду. (В std/math есть gcd/lcm — пишем свои.)
proc myGcd(a, b: int): int =
  if b == 0: a else: myGcd(b, a mod b)

proc myLcm(a, b: int): int = a div myGcd(a, b) * b

echo "GCD(48, 18) = ", myGcd(48, 18)
echo "LCM(48, 18) = ", myLcm(48, 18)
