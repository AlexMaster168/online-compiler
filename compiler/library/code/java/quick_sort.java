// Быстрая сортировка (разбиение Ломуто): в среднем O(n log n), в худшем O(n^2).
import java.util.Arrays;
import java.util.stream.Collectors;

public class Main {
    static void swap(int[] a, int i, int j) {
        int t = a[i];
        a[i] = a[j];
        a[j] = t;
    }

    static int partition(int[] a, int lo, int hi) {
        int pivot = a[hi], i = lo;
        for (int j = lo; j < hi; j++) {
            if (a[j] < pivot) swap(a, i++, j);
        }
        swap(a, i, hi);
        return i;
    }

    static void quickSort(int[] a, int lo, int hi) {
        if (lo >= hi) return;
        int p = partition(a, lo, hi);
        quickSort(a, lo, p - 1);
        quickSort(a, p + 1, hi);
    }

    public static void main(String[] args) {
        int[] a = {10, 7, 8, 9, 1, 5, 3};
        quickSort(a, 0, a.length - 1);
        System.out.println("Sorted: " + Arrays.stream(a).mapToObj(String::valueOf).collect(Collectors.joining(" ")));
    }
}
