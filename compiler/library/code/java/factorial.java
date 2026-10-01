// Факториал рекурсией. 20! — предел long; дальше нужен BigInteger.
public class Main {
    static long factorial(int n) {
        return n <= 1 ? 1 : n * factorial(n - 1);
    }

    public static void main(String[] args) {
        System.out.println("10! = " + factorial(10));
        System.out.println("20! = " + factorial(20));
    }
}
