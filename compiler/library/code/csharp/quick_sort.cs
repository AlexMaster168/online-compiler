// Быстрая сортировка (разбиение Ломуто): в среднем O(n log n), в худшем O(n^2).
using System;

class Program
{
    static int Partition(int[] a, int lo, int hi)
    {
        int pivot = a[hi], i = lo;
        for (int j = lo; j < hi; j++)
        {
            if (a[j] < pivot)
            {
                (a[i], a[j]) = (a[j], a[i]);
                i++;
            }
        }
        (a[i], a[hi]) = (a[hi], a[i]);
        return i;
    }

    static void QuickSort(int[] a, int lo, int hi)
    {
        if (lo >= hi) return;
        int p = Partition(a, lo, hi);
        QuickSort(a, lo, p - 1);
        QuickSort(a, p + 1, hi);
    }

    static void Main()
    {
        int[] a = { 10, 7, 8, 9, 1, 5, 3 };
        QuickSort(a, 0, a.Length - 1);
        Console.WriteLine("Sorted: " + string.Join(" ", a));
    }
}
