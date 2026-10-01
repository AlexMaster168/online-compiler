// Сортировка пузырьком: O(n^2). Если за проход не было обменов — массив уже отсортирован.
import java.util.Arrays;
import java.util.stream.Collectors;

public class Main {
    static void bubbleSort(int[] a) {
        for (int i = 0; i < a.length - 1; i++) {
            boolean swapped = false;
            for (int j = 0; j < a.length - 1 - i; j++) {
                if (a[j] > a[j + 1]) {
                    int t = a[j];
                    a[j] = a[j + 1];
                    a[j + 1] = t;
                    swapped = true;
                }
            }
            if (!swapped) break;
        }
    }

    public static void main(String[] args) {
        int[] a = {5, 2, 9, 1, 5, 6};
        bubbleSort(a);
        System.out.println("Sorted: " + Arrays.stream(a).mapToObj(String::valueOf).collect(Collectors.joining(" ")));
    }
}
