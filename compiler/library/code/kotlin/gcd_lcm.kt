// НОД по Евклиду: gcd(a, b) = gcd(b, a mod b). tailrec — компилятор превратит рекурсию в цикл.
tailrec fun gcd(a: Long, b: Long): Long = if (b == 0L) a else gcd(b, a % b)

fun lcm(a: Long, b: Long): Long = a / gcd(a, b) * b

fun main() {
    println("GCD(48, 18) = ${gcd(48, 18)}")
    println("LCM(48, 18) = ${lcm(48, 18)}")
}
