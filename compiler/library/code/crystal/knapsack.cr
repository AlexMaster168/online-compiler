# Рюкзак 0/1: dp[c] — лучшая ценность при вместимости c; downto — цикл сверху вниз.
def knapsack(items : Array({Int32, Int32}), capacity : Int32) : Int32
  dp = Array.new(capacity + 1, 0)
  items.each do |(w, v)|
    capacity.downto(w) { |c| dp[c] = {dp[c], dp[c - w] + v}.max }
  end
  dp[capacity]
end

puts "Knapsack max value: #{knapsack([{1, 1}, {3, 4}, {4, 5}, {5, 7}], 7)}"
