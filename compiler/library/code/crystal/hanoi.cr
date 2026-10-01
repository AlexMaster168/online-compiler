# Ханойские башни: 2^n - 1 ходов. Метод возвращает число ходов.
def hanoi(n : Int32, source : Char, spare : Char, target : Char) : Int32
  return 0 if n == 0
  before = hanoi(n - 1, source, target, spare)
  puts "Move disk #{n} from #{source} to #{target}"
  before + 1 + hanoi(n - 1, spare, source, target)
end

puts "Total moves: #{hanoi(3, 'A', 'B', 'C')}"
