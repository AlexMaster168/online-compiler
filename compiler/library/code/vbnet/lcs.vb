' Наибольшая общая подпоследовательность: dp(i, j) — длина LCS для префиксов. O(n * m).
Module Program
    Function Lcs(a As String, b As String) As Integer
        Dim dp(a.Length, b.Length) As Integer
        For i As Integer = 1 To a.Length
            For j As Integer = 1 To b.Length
                If a(i - 1) = b(j - 1) Then
                    dp(i, j) = dp(i - 1, j - 1) + 1
                Else
                    dp(i, j) = Math.Max(dp(i - 1, j), dp(i, j - 1))
                End If
            Next
        Next
        Return dp(a.Length, b.Length)
    End Function

    Sub Main()
        Console.WriteLine($"LCS(ABCBDAB, BDCABA) = {Lcs("ABCBDAB", "BDCABA")}")
    End Sub
End Module
