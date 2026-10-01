-- Быстрая сортировка: классика Haskell — опора, меньшие слева, остальные справа.
-- Не на месте (в отличие от Ломуто), зато в три строки. В среднем O(n log n).
quickSort :: [Int] -> [Int]
quickSort [] = []
quickSort (pivot : rest) = quickSort smaller ++ [pivot] ++ quickSort larger
  where
    smaller = [x | x <- rest, x < pivot]
    larger = [x | x <- rest, x >= pivot]

main :: IO ()
main = putStrLn $ "Sorted: " ++ unwords (map show (quickSort [10, 7, 8, 9, 1, 5, 3]))
