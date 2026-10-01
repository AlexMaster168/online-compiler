// Сортировка слиянием: всегда O(n log n), стабильная.
import java.util.Arrays;
import java.util.stream.Collectors;

public class Main {
    static int[] mergeSort(int[] a) {
        if (a.length <= 1) return a;
        int mid = a.length / 2;
        int[] left = mergeSort(Arrays.copyOfRange(a, 0, mid));
        int[] right = mergeSort(Arrays.copyOfRange(a, mid, a.length));
        int[] merged = new int[a.length];
        int i = 0, j = 0, k = 0;
        while (i < left.length && j < right.length) merged[k++] = left[i] <= right[j] ? left[i++] : right[j++];
        while (i < left.length) merged[k++] = left[i++];
        while (j < right.length) merged[k++] = right[j++];
        return merged;
    }

    public static void main(String[] args) {
        int[] sorted = mergeSort(new int[] {38, 27, 43, 3, 9, 82, 10});
        System.out.println("Sorted: " + Arrays.stream(sorted).mapToObj(String::valueOf).collect(Collectors.joining(" ")));
    }
}
