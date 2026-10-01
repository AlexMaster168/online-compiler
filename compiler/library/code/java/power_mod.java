// Быстрое возведение в степень: O(log n). (Есть BigInteger.modPow — здесь пишем руками.)
public class Main {
    static final long MOD = 1_000_000_007L;

    static long powerMod(long base, long exp, long mod) {
        long result = 1;
        base %= mod;
        while (exp > 0) {
            if ((exp & 1) == 1) result = result * base % mod;
            base = base * base % mod;
            exp >>= 1;
        }
        return result;
    }

    public static void main(String[] args) {
        System.out.println("2^30 mod " + MOD + " = " + powerMod(2, 30, MOD));
        System.out.println("3^200 mod " + MOD + " = " + powerMod(3, 200, MOD));
    }
}
