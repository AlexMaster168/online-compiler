// НОД по Евклиду: хвостовая рекурсия.
import scala.annotation.tailrec

object Main:
  @tailrec
  def gcd(a: Long, b: Long): Long = if b == 0 then a else gcd(b, a % b)
  def lcm(a: Long, b: Long): Long = a / gcd(a, b) * b

  def main(args: Array[String]): Unit =
    println(s"GCD(48, 18) = ${gcd(48, 18)}")
    println(s"LCM(48, 18) = ${lcm(48, 18)}")
