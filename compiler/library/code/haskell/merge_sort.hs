-- Сортировка слиянием: всегда O(n log n), стабильная.
merge :: [Int] -> [Int] -> [Int]
merge [] ys = ys
merge xs [] = xs
merge (x : xs) (y : ys)
  | x <= y = x : merge xs (y : ys)
  | otherwise = y : merge (x : xs) ys

mergeSort :: [Int] -> [Int]
mergeSort xs
  | length xs <= 1 = xs
  | otherwise = merge (mergeSort left) (mergeSort right)
  where
    (left, right) = splitAt (length xs `div` 2) xs

main :: IO ()
main = putStrLn $ "Sorted: " ++ unwords (map show (mergeSort [38, 27, 43, 3, 9, 82, 10]))
