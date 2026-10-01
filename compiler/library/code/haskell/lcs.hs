-- Наибольшая общая подпоследовательность: ленивый массив dp ссылается сам на себя — мемоизация даром.
import Data.Array

lcs :: String -> String -> Int
lcs a b = table ! (n, m)
  where
    n = length a
    m = length b
    xs = listArray (1, n) a
    ys = listArray (1, m) b
    table = array ((0, 0), (n, m)) [((i, j), cell i j) | i <- [0 .. n], j <- [0 .. m]]
    cell 0 _ = 0
    cell _ 0 = 0
    cell i j
      | xs ! i == ys ! j = table ! (i - 1, j - 1) + 1
      | otherwise = max (table ! (i - 1, j)) (table ! (i, j - 1))

main :: IO ()
main = putStrLn $ "LCS(ABCBDAB, BDCABA) = " ++ show (lcs "ABCBDAB" "BDCABA")
