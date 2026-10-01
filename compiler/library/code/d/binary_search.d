// Бинарный поиск: O(log n). ptrdiff_t — знаковый размер, чтобы вернуть -1.
import std.stdio;

ptrdiff_t binarySearch(const int[] a, int target)
{
    ptrdiff_t lo = 0, hi = cast(ptrdiff_t) a.length - 1;
    while (lo <= hi)
    {
        immutable mid = (lo + hi) / 2;
        if (a[mid] == target)
            return mid;
        if (a[mid] < target)
            lo = mid + 1;
        else
            hi = mid - 1;
    }
    return -1;
}

void main()
{
    immutable arr = [1, 3, 5, 7, 9, 11, 13, 15, 17, 19];
    foreach (target; [7, 4])
    {
        immutable i = binarySearch(arr, target);
        if (i >= 0)
            writefln("Found %d at index %d", target, i);
        else
            writefln("%d not found", target);
    }
}
