# Рюкзак 0/1: dp[c] — лучшая ценность при вместимости c; c идёт сверху вниз.
def knapsack(weights, values, capacity)
  dp = Array.new(capacity + 1, 0)
  weights.zip(values).each do |w, v|
    capacity.downto(w) { |c| dp[c] = [dp[c], dp[c - w] + v].max }
  end
  dp[capacity]
end

puts "Knapsack max value: #{knapsack([1, 3, 4, 5], [1, 4, 5, 7], 7)}"
