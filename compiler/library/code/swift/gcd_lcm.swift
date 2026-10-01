// НОД по Евклиду: gcd(a, b) = gcd(b, a mod b). НОК = a / gcd * b.
func gcd(_ a: Int, _ b: Int) -> Int { b == 0 ? a : gcd(b, a % b) }
func lcm(_ a: Int, _ b: Int) -> Int { a / gcd(a, b) * b }

print("GCD(48, 18) = \(gcd(48, 18))")
print("LCM(48, 18) = \(lcm(48, 18))")
