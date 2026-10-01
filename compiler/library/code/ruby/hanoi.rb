# Ханойские башни: 2^n - 1 ходов. Возвращаем число ходов.
def hanoi(n, source, spare, target)
  return 0 if n.zero?

  before = hanoi(n - 1, source, target, spare)
  puts "Move disk #{n} from #{source} to #{target}"
  before + 1 + hanoi(n - 1, spare, source, target)
end

puts "Total moves: #{hanoi(3, 'A', 'B', 'C')}"
