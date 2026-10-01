# Наибольшая общая подпоследовательность: dp[i][j] — длина LCS для префиксов. O(n * m).
def lcs(a, b)
  dp = Array.new(a.size + 1) { Array.new(b.size + 1, 0) }
  (1..a.size).each do |i|
    (1..b.size).each do |j|
      dp[i][j] = a[i - 1] == b[j - 1] ? dp[i - 1][j - 1] + 1 : [dp[i - 1][j], dp[i][j - 1]].max
    end
  end
  dp[a.size][b.size]
end

puts "LCS(ABCBDAB, BDCABA) = #{lcs('ABCBDAB', 'BDCABA')}"
