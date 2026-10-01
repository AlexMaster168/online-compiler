' Быстрое возведение в степень: O(log n). And — побитовое И для чисел.
Module Program
    Const Modulus As Long = 1000000007

    Function PowerMod(b As Long, e As Long, m As Long) As Long
        Dim result As Long = 1
        b = b Mod m
        While e > 0
            If (e And 1) = 1 Then result = result * b Mod m
            b = b * b Mod m
            e >>= 1
        End While
        Return result
    End Function

    Sub Main()
        Console.WriteLine($"2^30 mod {Modulus} = {PowerMod(2, 30, Modulus)}")
        Console.WriteLine($"3^200 mod {Modulus} = {PowerMod(3, 200, Modulus)}")
    End Sub
End Module
