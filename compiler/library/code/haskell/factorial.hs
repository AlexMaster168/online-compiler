-- Факториал рекурсией с сопоставлением с образцом. Integer — длинная арифметика без переполнения.
factorial :: Integer -> Integer
factorial 0 = 1
factorial n = n * factorial (n - 1)

main :: IO ()
main = do
  putStrLn $ "10! = " ++ show (factorial 10)
  putStrLn $ "20! = " ++ show (factorial 20)
