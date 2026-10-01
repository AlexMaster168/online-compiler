// Бинарный поиск: O(log n). (lo + hi) >>> 1 — без переполнения int.
public class Main {
    static int binarySearch(int[] a, int target) {
        int lo = 0, hi = a.length - 1;
        while (lo <= hi) {
            int mid = (lo + hi) >>> 1;
            if (a[mid] == target) return mid;
            if (a[mid] < target) lo = mid + 1;
            else hi = mid - 1;
        }
        return -1;
    }

    public static void main(String[] args) {
        int[] a = {1, 3, 5, 7, 9, 11, 13, 15, 17, 19};
        for (int target : new int[] {7, 4}) {
            int i = binarySearch(a, target);
            System.out.println(i >= 0 ? "Found " + target + " at index " + i : target + " not found");
        }
    }
}
