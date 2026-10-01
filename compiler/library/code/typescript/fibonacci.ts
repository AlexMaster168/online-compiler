// Числа Фибоначчи итеративно, O(n). bigint — чтобы не упереться в точность number.
function fib(n: number): bigint {
  let a = 0n;
  let b = 1n;
  for (let i = 0; i < n; i++) [a, b] = [b, a + b];
  return a;
}

console.log("Fibonacci: " + Array.from({ length: 15 }, (_, i) => fib(i)).join(" "));
console.log(`F(50) = ${fib(50)}`);
