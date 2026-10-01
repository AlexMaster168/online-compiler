-- Рюкзак 0/1: строка dp пересчитывается для каждого предмета (свёртка по предметам).
knapsack :: [(Int, Int)] -> Int -> Int
knapsack items capacity = last (foldl step (replicate (capacity + 1) 0) items)
  where
    step dp (w, v) = [if c >= w then max (dp !! c) (dp !! (c - w) + v) else dp !! c | c <- [0 .. capacity]]

main :: IO ()
main = putStrLn $ "Knapsack max value: " ++ show (knapsack (zip [1, 3, 4, 5] [1, 4, 5, 7]) 7)
