' НОД по Евклиду: gcd(a, b) = gcd(b, a Mod b). НОК = a \ gcd * b.
Module Program
    Function Gcd(a As Long, b As Long) As Long
        Return If(b = 0, a, Gcd(b, a Mod b))
    End Function

    Function Lcm(a As Long, b As Long) As Long
        ' Скобки обязательны: в VB целочисленное деление \ слабее умножения,
        ' и a \ Gcd(a, b) * b посчиталось бы как a \ (Gcd(a, b) * b)
        Return (a \ Gcd(a, b)) * b
    End Function

    Sub Main()
        Console.WriteLine($"GCD(48, 18) = {Gcd(48, 18)}")
        Console.WriteLine($"LCM(48, 18) = {Lcm(48, 18)}")
    End Sub
End Module
