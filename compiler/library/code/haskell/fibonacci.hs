-- Числа Фибоначчи бесконечным ленивым списком: каждый элемент — сумма двух предыдущих.
fibs :: [Integer]
fibs = 0 : 1 : zipWith (+) fibs (tail fibs)

main :: IO ()
main = do
  putStrLn $ "Fibonacci: " ++ unwords (map show (take 15 fibs))
  putStrLn $ "F(50) = " ++ show (fibs !! 50)
