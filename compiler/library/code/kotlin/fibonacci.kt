// Числа Фибоначчи ленивой последовательностью generateSequence.
val fibonacci: Sequence<Long> = generateSequence(0L to 1L) { (a, b) -> b to a + b }.map { it.first }

fun main() {
    println("Fibonacci: " + fibonacci.take(15).joinToString(" "))
    println("F(50) = ${fibonacci.elementAt(50)}")
}
