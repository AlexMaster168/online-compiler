// НОД по Евклиду: gcd(a, b) = gcd(b, a mod b). НОК = a / gcd * b.
public class Main {
    static long gcd(long a, long b) {
        return b == 0 ? a : gcd(b, a % b);
    }

    static long lcm(long a, long b) {
        return a / gcd(a, b) * b;
    }

    public static void main(String[] args) {
        System.out.println("GCD(48, 18) = " + gcd(48, 18));
        System.out.println("LCM(48, 18) = " + lcm(48, 18));
    }
}
