// НОД по Евклиду: gcd(a, b) = gcd(b, a mod b). НОК = a / gcd * b.
const gcd = (a: number, b: number): number => (b === 0 ? a : gcd(b, a % b));
const lcm = (a: number, b: number): number => (a / gcd(a, b)) * b;

console.log(`GCD(48, 18) = ${gcd(48, 18)}`);
console.log(`LCM(48, 18) = ${lcm(48, 18)}`);
