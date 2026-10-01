// НОД по Евклиду: gcd(a, b) = gcd(b, a mod b). НОК = a / gcd * b.
const gcd = (a, b) => (b === 0 ? a : gcd(b, a % b));
const lcm = (a, b) => (a / gcd(a, b)) * b;

console.log(`GCD(48, 18) = ${gcd(48, 18)}`);
console.log(`LCM(48, 18) = ${lcm(48, 18)}`);
