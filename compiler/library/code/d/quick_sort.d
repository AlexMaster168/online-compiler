// Быстрая сортировка (разбиение Ломуто) на срезах: срез смотрит в тот же массив, копий нет.
import std.algorithm : swap;
import std.stdio;

size_t partition(int[] a)
{
    immutable pivot = a[$ - 1];  // $ — длина среза
    size_t i = 0;
    foreach (j; 0 .. a.length - 1)
    {
        if (a[j] < pivot)
            swap(a[i++], a[j]);
    }
    swap(a[i], a[$ - 1]);
    return i;
}

void quickSort(int[] a)
{
    if (a.length < 2)
        return;
    immutable p = partition(a);
    quickSort(a[0 .. p]);
    quickSort(a[p + 1 .. $]);
}

void main()
{
    auto a = [10, 7, 8, 9, 1, 5, 3];
    quickSort(a);
    writefln("Sorted: %(%s %)", a);
}
