// Ханойские башни: 2^n - 1 ходов. Возвращаем число ходов вместо глобального счётчика.
fn hanoi(n: u32, source: char, spare: char, target: char) -> u32 {
    if n == 0 {
        return 0;
    }
    let before = hanoi(n - 1, source, target, spare);
    println!("Move disk {n} from {source} to {target}");
    before + 1 + hanoi(n - 1, spare, source, target)
}

fn main() {
    let moves = hanoi(3, 'A', 'B', 'C');
    println!("Total moves: {moves}");
}
