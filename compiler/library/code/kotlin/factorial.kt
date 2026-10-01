// Факториал рекурсией. 20! — предел Long.
fun factorial(n: Int): Long = if (n <= 1) 1L else n * factorial(n - 1)

fun main() {
    println("10! = ${factorial(10)}")
    println("20! = ${factorial(20)}")
}
