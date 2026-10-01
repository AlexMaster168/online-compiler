// Ханойские башни: 2^n - 1 ходов.
let moves = 0;

function hanoi(n, source, spare, target) {
  if (n === 0) return;
  hanoi(n - 1, source, target, spare);
  console.log(`Move disk ${n} from ${source} to ${target}`);
  moves++;
  hanoi(n - 1, spare, source, target);
}

hanoi(3, "A", "B", "C");
console.log("Total moves: " + moves);
