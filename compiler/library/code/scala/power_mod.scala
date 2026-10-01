// Быстрое возведение в степень: O(log n).
object Main:
  val Mod = 1_000_000_007L

  def powerMod(base: Long, exp: Long, m: Long): Long =
    var result = 1L
    var b = base % m
    var e = exp
    while e > 0 do
      if (e & 1) == 1 then result = result * b % m
      b = b * b % m
      e >>= 1
    result

  def main(args: Array[String]): Unit =
    println(s"2^30 mod $Mod = ${powerMod(2, 30, Mod)}")
    println(s"3^200 mod $Mod = ${powerMod(3, 200, Mod)}")
