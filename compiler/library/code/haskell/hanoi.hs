-- Ханойские башни: функция возвращает список ходов, печать — отдельно от логики.
hanoi :: Int -> String -> String -> String -> [(Int, String, String)]
hanoi 0 _ _ _ = []
hanoi n source spare target =
  hanoi (n - 1) source target spare ++ [(n, source, target)] ++ hanoi (n - 1) spare source target

main :: IO ()
main = do
  let moves = hanoi 3 "A" "B" "C"
  mapM_ (\(n, from, to) -> putStrLn $ "Move disk " ++ show n ++ " from " ++ from ++ " to " ++ to) moves
  putStrLn $ "Total moves: " ++ show (length moves)
