' Быстрая сортировка (разбиение Ломуто). ByRef — параметр по ссылке, как ref в C#.
Module Program
    Sub Swap(ByRef x As Integer, ByRef y As Integer)
        Dim t As Integer = x
        x = y
        y = t
    End Sub

    Sub QuickSort(a As Integer(), lo As Integer, hi As Integer)
        If lo >= hi Then Return
        Dim pivot As Integer = a(hi)
        Dim i As Integer = lo
        For j As Integer = lo To hi - 1
            If a(j) < pivot Then
                Swap(a(i), a(j))
                i += 1
            End If
        Next
        Swap(a(i), a(hi))
        QuickSort(a, lo, i - 1)
        QuickSort(a, i + 1, hi)
    End Sub

    Sub Main()
        Dim a As Integer() = {10, 7, 8, 9, 1, 5, 3}
        QuickSort(a, 0, a.Length - 1)
        Console.WriteLine("Sorted: " & String.Join(" ", a))
    End Sub
End Module
