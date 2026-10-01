// Решето Эратосфена: O(n log log n). BitSet — по биту на число.
import java.util.BitSet;
import java.util.StringJoiner;

public class Main {
    public static void main(String[] args) {
        int n = 50;
        BitSet composite = new BitSet(n + 1);
        StringJoiner primes = new StringJoiner(" ");
        for (int p = 2; p <= n; p++) {
            if (composite.get(p)) continue;
            primes.add(String.valueOf(p));
            for (int k = p * p; k <= n; k += p) composite.set(k);
        }
        System.out.println("Primes up to " + n + ": " + primes);
    }
}
