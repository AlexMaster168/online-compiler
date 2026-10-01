# Наибольшая общая подпоследовательность: матрица dp размером (n+1) x (m+1).
function lcs(a, b)
    dp = zeros(Int, length(a) + 1, length(b) + 1)
    for i in 1:length(a), j in 1:length(b)
        dp[i+1, j+1] = a[i] == b[j] ? dp[i, j] + 1 : max(dp[i, j+1], dp[i+1, j])
    end
    dp[end, end]
end

println("LCS(ABCBDAB, BDCABA) = ", lcs("ABCBDAB", "BDCABA"))
