// Сортировка слиянием: всегда O(n log n), стабильная. Срезы массивов a[..mid] — C# 8+.
using System;
using System.Collections.Generic;

class Program
{
    static int[] MergeSort(int[] a)
    {
        if (a.Length <= 1) return a;
        int mid = a.Length / 2;
        int[] left = MergeSort(a[..mid]), right = MergeSort(a[mid..]);
        var merged = new List<int>(a.Length);
        int i = 0, j = 0;
        while (i < left.Length && j < right.Length) merged.Add(left[i] <= right[j] ? left[i++] : right[j++]);
        while (i < left.Length) merged.Add(left[i++]);
        while (j < right.Length) merged.Add(right[j++]);
        return merged.ToArray();
    }

    static void Main()
    {
        Console.WriteLine("Sorted: " + string.Join(" ", MergeSort(new[] { 38, 27, 43, 3, 9, 82, 10 })));
    }
}
