// Рюкзак 0/1: dp[c] — лучшая ценность при вместимости c; c идёт сверху вниз.
public class Main {
    static int knapsack(int[] weights, int[] values, int capacity) {
        int[] dp = new int[capacity + 1];
        for (int i = 0; i < weights.length; i++) {
            for (int c = capacity; c >= weights[i]; c--) {
                dp[c] = Math.max(dp[c], dp[c - weights[i]] + values[i]);
            }
        }
        return dp[capacity];
    }

    public static void main(String[] args) {
        System.out.println("Knapsack max value: " + knapsack(new int[] {1, 3, 4, 5}, new int[] {1, 4, 5, 7}, 7));
    }
}
