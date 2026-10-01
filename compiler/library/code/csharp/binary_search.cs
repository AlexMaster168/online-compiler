// Бинарный поиск: O(log n). (Есть Array.BinarySearch — здесь пишем руками.)
using System;

class Program
{
    static int BinarySearch(int[] a, int target)
    {
        int lo = 0, hi = a.Length - 1;
        while (lo <= hi)
        {
            int mid = lo + (hi - lo) / 2;
            if (a[mid] == target) return mid;
            if (a[mid] < target) lo = mid + 1;
            else hi = mid - 1;
        }
        return -1;
    }

    static void Main()
    {
        int[] a = { 1, 3, 5, 7, 9, 11, 13, 15, 17, 19 };
        foreach (int target in new[] { 7, 4 })
        {
            int i = BinarySearch(a, target);
            Console.WriteLine(i >= 0 ? $"Found {target} at index {i}" : $"{target} not found");
        }
    }
}
