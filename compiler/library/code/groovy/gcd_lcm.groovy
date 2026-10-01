// НОД по Евклиду: gcd(a, b) = gcd(b, a % b). НОК = a / gcd * b.
long gcd(long a, long b) { b == 0 ? a : gcd(b, a % b) }
long lcm(long a, long b) { a.intdiv(gcd(a, b)) * b }

println "GCD(48, 18) = ${gcd(48, 18)}"
println "LCM(48, 18) = ${lcm(48, 18)}"
