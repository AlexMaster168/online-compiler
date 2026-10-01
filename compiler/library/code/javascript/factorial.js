// Факториал рекурсией: n! = n * (n - 1)!. 20! > 2^53, поэтому BigInt.
const factorial = (n) => (n <= 1n ? 1n : n * factorial(n - 1n));

console.log(`10! = ${factorial(10n)}`);
console.log(`20! = ${factorial(20n)}`);
