// Ханойские башни: 2^n - 1 ходов.
public class Main {
    static int moves = 0;

    static void hanoi(int n, char source, char spare, char target) {
        if (n == 0) return;
        hanoi(n - 1, source, target, spare);
        System.out.println("Move disk " + n + " from " + source + " to " + target);
        moves++;
        hanoi(n - 1, spare, source, target);
    }

    public static void main(String[] args) {
        hanoi(3, 'A', 'B', 'C');
        System.out.println("Total moves: " + moves);
    }
}
