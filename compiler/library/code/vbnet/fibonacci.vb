' Числа Фибоначчи итератором: Iterator Function + Yield отдают значения лениво.
Imports System.Collections.Generic
Imports System.Linq

Module Program
    Iterator Function Fibonacci() As IEnumerable(Of Long)
        Dim a As Long = 0, b As Long = 1
        Do
            Yield a
            Dim t As Long = a + b
            a = b
            b = t
        Loop
    End Function

    Sub Main()
        Console.WriteLine("Fibonacci: " & String.Join(" ", Fibonacci().Take(15)))
        Console.WriteLine($"F(50) = {Fibonacci().ElementAt(50)}")
    End Sub
End Module
