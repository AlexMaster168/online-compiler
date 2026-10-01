' Факториал рекурсией. 20! — предел Long (64 бита).
Module Program
    Function Factorial(n As Integer) As Long
        If n <= 1 Then Return 1
        Return n * Factorial(n - 1)
    End Function

    Sub Main()
        Console.WriteLine($"10! = {Factorial(10)}")
        Console.WriteLine($"20! = {Factorial(20)}")
    End Sub
End Module
