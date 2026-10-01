' Ханойские башни: 2^n - 1 ходов. Функция возвращает число ходов.
Module Program
    Function Hanoi(n As Integer, source As Char, spare As Char, target As Char) As Integer
        If n = 0 Then Return 0
        Dim before As Integer = Hanoi(n - 1, source, target, spare)
        Console.WriteLine($"Move disk {n} from {source} to {target}")
        Return before + 1 + Hanoi(n - 1, spare, source, target)
    End Function

    Sub Main()
        Console.WriteLine("Total moves: " & Hanoi(3, "A"c, "B"c, "C"c))
    End Sub
End Module
