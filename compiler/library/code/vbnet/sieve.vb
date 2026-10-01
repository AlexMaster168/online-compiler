' Решето Эратосфена: O(n log log n). Step — шаг цикла For.
Imports System.Collections.Generic

Module Program
    Function Sieve(n As Integer) As List(Of Integer)
        Dim composite(n) As Boolean  ' в VB размер массива — это последний индекс
        Dim primes As New List(Of Integer)
        For p As Integer = 2 To n
            If composite(p) Then Continue For
            primes.Add(p)
            For k As Integer = p * p To n Step p
                composite(k) = True
            Next
        Next
        Return primes
    End Function

    Sub Main()
        Console.WriteLine("Primes up to 50: " & String.Join(" ", Sieve(50)))
    End Sub
End Module
