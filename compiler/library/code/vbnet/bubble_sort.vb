' Сортировка пузырьком: O(n^2). Если за проход не было обменов — массив уже отсортирован.
Module Program
    Sub BubbleSort(a As Integer())
        For i As Integer = 0 To a.Length - 2
            Dim swapped As Boolean = False
            For j As Integer = 0 To a.Length - 2 - i
                If a(j) > a(j + 1) Then
                    Dim t As Integer = a(j)
                    a(j) = a(j + 1)
                    a(j + 1) = t
                    swapped = True
                End If
            Next
            If Not swapped Then Exit For
        Next
    End Sub

    Sub Main()
        Dim a As Integer() = {5, 2, 9, 1, 5, 6}
        BubbleSort(a)
        Console.WriteLine("Sorted: " & String.Join(" ", a))
    End Sub
End Module
