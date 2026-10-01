// Числа Фибоначчи итеративно, O(n). BigInt — чтобы не упереться в точность double на больших n.
function fib(n) {
  let a = 0n, b = 1n;
  for (let i = 0; i < n; i++) [a, b] = [b, a + b];
  return a;
}

console.log("Fibonacci: " + Array.from({ length: 15 }, (_, i) => fib(i)).join(" "));
console.log(`F(50) = ${fib(50)}`);
