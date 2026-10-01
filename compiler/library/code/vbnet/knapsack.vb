' Рюкзак 0/1: dp(c) — лучшая ценность при вместимости c; c идёт сверху вниз (Step -1).
Module Program
    Function Knapsack(weights As Integer(), values As Integer(), capacity As Integer) As Integer
        Dim dp(capacity) As Integer
        For i As Integer = 0 To weights.Length - 1
            For c As Integer = capacity To weights(i) Step -1
                dp(c) = Math.Max(dp(c), dp(c - weights(i)) + values(i))
            Next
        Next
        Return dp(capacity)
    End Function

    Sub Main()
        Console.WriteLine("Knapsack max value: " & Knapsack({1, 3, 4, 5}, {1, 4, 5, 7}, 7))
    End Sub
End Module
