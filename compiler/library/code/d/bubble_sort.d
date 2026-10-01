// Сортировка пузырьком: O(n^2). Если за проход не было обменов — массив уже отсортирован.
import std.algorithm : swap;
import std.stdio;

void bubbleSort(int[] a)
{
    foreach (i; 0 .. a.length - 1)
    {
        bool swapped = false;
        foreach (j; 0 .. a.length - 1 - i)
        {
            if (a[j] > a[j + 1])
            {
                swap(a[j], a[j + 1]);
                swapped = true;
            }
        }
        if (!swapped)
            break;
    }
}

void main()
{
    auto a = [5, 2, 9, 1, 5, 6];
    bubbleSort(a);
    writefln("Sorted: %(%s %)", a);  // %( ... %) — форматирование диапазона
}
