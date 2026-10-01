' Сортировка слиянием: всегда O(n log n), стабильная.
Imports System.Collections.Generic

Module Program
    Function MergeSort(a As List(Of Integer)) As List(Of Integer)
        If a.Count <= 1 Then Return a
        Dim mid As Integer = a.Count \ 2  ' \ — целочисленное деление
        Dim left = MergeSort(a.GetRange(0, mid))
        Dim right = MergeSort(a.GetRange(mid, a.Count - mid))
        Dim merged As New List(Of Integer)(a.Count)
        Dim i As Integer = 0, j As Integer = 0
        While i < left.Count AndAlso j < right.Count
            If left(i) <= right(j) Then
                merged.Add(left(i)) : i += 1
            Else
                merged.Add(right(j)) : j += 1
            End If
        End While
        merged.AddRange(left.GetRange(i, left.Count - i))
        merged.AddRange(right.GetRange(j, right.Count - j))
        Return merged
    End Function

    Sub Main()
        Dim sorted = MergeSort(New List(Of Integer) From {38, 27, 43, 3, 9, 82, 10})
        Console.WriteLine("Sorted: " & String.Join(" ", sorted))
    End Sub
End Module
