// Сортировка пузырьком: O(n^2). Если за проход не было обменов — массив уже отсортирован.
using System;

class Program
{
    static void BubbleSort(int[] a)
    {
        for (int i = 0; i < a.Length - 1; i++)
        {
            bool swapped = false;
            for (int j = 0; j < a.Length - 1 - i; j++)
            {
                if (a[j] > a[j + 1])
                {
                    (a[j], a[j + 1]) = (a[j + 1], a[j]);
                    swapped = true;
                }
            }
            if (!swapped) break;
        }
    }

    static void Main()
    {
        int[] a = { 5, 2, 9, 1, 5, 6 };
        BubbleSort(a);
        Console.WriteLine("Sorted: " + string.Join(" ", a));
    }
}
