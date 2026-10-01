-- НОД по Евклиду: gcd(a, b) = gcd(b, a mod b). (В Prelude есть gcd/lcm — пишем свои.)
gcd' :: Int -> Int -> Int
gcd' a 0 = a
gcd' a b = gcd' b (a `mod` b)

lcm' :: Int -> Int -> Int
lcm' a b = a `div` gcd' a b * b

main :: IO ()
main = do
  putStrLn $ "GCD(48, 18) = " ++ show (gcd' 48 18)
  putStrLn $ "LCM(48, 18) = " ++ show (lcm' 48 18)
