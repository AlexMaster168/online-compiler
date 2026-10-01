// Числа Фибоначчи итеративно, O(n). F(50) не влезает в int — long.
import java.util.StringJoiner;

public class Main {
    static long fib(int n) {
        long a = 0, b = 1;
        for (int i = 0; i < n; i++) {
            long t = a + b;
            a = b;
            b = t;
        }
        return a;
    }

    public static void main(String[] args) {
        StringJoiner first = new StringJoiner(" ");
        for (int i = 0; i < 15; i++) first.add(String.valueOf(fib(i)));
        System.out.println("Fibonacci: " + first);
        System.out.println("F(50) = " + fib(50));
    }
}
