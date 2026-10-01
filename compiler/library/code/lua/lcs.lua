-- Наибольшая общая подпоследовательность: dp[i][j] — длина LCS для префиксов. O(n * m).
local function lcs(a, b)
  local dp = {}
  for i = 0, #a do
    dp[i] = {}
    for j = 0, #b do dp[i][j] = 0 end
  end
  for i = 1, #a do
    for j = 1, #b do
      if a:sub(i, i) == b:sub(j, j) then
        dp[i][j] = dp[i - 1][j - 1] + 1
      else
        dp[i][j] = math.max(dp[i - 1][j], dp[i][j - 1])
      end
    end
  end
  return dp[#a][#b]
end

print("LCS(ABCBDAB, BDCABA) = " .. lcs("ABCBDAB", "BDCABA"))
