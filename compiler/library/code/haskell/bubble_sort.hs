-- Сортировка пузырьком: O(n^2). В Haskell данные неизменяемые — каждый проход строит новый список.
bubblePass :: [Int] -> ([Int], Bool)
bubblePass (x : y : rest)
  | x > y = let (rest', _) = bubblePass (x : rest) in (y : rest', True)
  | otherwise = let (rest', swapped) = bubblePass (y : rest) in (x : rest', swapped)
bubblePass xs = (xs, False)

bubbleSort :: [Int] -> [Int]
bubbleSort xs = case bubblePass xs of
  (ys, True) -> bubbleSort ys
  (ys, False) -> ys

main :: IO ()
main = putStrLn $ "Sorted: " ++ unwords (map show (bubbleSort [5, 2, 9, 1, 5, 6]))
