-- Быстрое возведение в степень: O(log n). Делим показатель пополам рекурсивно.
modulus :: Integer
modulus = 1000000007

powerMod :: Integer -> Integer -> Integer -> Integer
powerMod _ 0 _ = 1
powerMod base ex m
  | even ex = half * half `mod` m
  | otherwise = base * powerMod base (ex - 1) m `mod` m
  where
    half = powerMod base (ex `div` 2) m

main :: IO ()
main = do
  putStrLn $ "2^30 mod " ++ show modulus ++ " = " ++ show (powerMod 2 30 modulus)
  putStrLn $ "3^200 mod " ++ show modulus ++ " = " ++ show (powerMod 3 200 modulus)
