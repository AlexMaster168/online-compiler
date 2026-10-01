// Сортировка слиянием: всегда O(n log n), стабильная. ~ — конкатенация массивов.
import std.stdio;

int[] mergeSort(int[] a)
{
    if (a.length <= 1)
        return a;
    auto left = mergeSort(a[0 .. $ / 2]);
    auto right = mergeSort(a[$ / 2 .. $]);
    int[] merged;
    while (left.length && right.length)
    {
        if (left[0] <= right[0])
        {
            merged ~= left[0];
            left = left[1 .. $];
        }
        else
        {
            merged ~= right[0];
            right = right[1 .. $];
        }
    }
    return merged ~ left ~ right;
}

void main()
{
    writefln("Sorted: %(%s %)", mergeSort([38, 27, 43, 3, 9, 82, 10]));
}
