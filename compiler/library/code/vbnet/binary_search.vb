' Бинарный поиск: O(log n), массив обязан быть отсортирован.
Module Program
    Function BinarySearch(a As Integer(), target As Integer) As Integer
        Dim lo As Integer = 0, hi As Integer = a.Length - 1
        While lo <= hi
            Dim mid As Integer = (lo + hi) \ 2
            If a(mid) = target Then Return mid
            If a(mid) < target Then
                lo = mid + 1
            Else
                hi = mid - 1
            End If
        End While
        Return -1
    End Function

    Sub Main()
        Dim arr As Integer() = {1, 3, 5, 7, 9, 11, 13, 15, 17, 19}
        For Each target As Integer In {7, 4}
            Dim i As Integer = BinarySearch(arr, target)
            If i >= 0 Then
                Console.WriteLine($"Found {target} at index {i}")
            Else
                Console.WriteLine($"{target} not found")
            End If
        Next
    End Sub
End Module
