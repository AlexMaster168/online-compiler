-- Решето Эратосфена на изменяемом массиве в монаде ST: O(n log log n), снаружи — чистая функция.
import Control.Monad (forM_, when)
import Data.Array.ST (newArray, readArray, runSTUArray, writeArray)
import Data.Array.Unboxed (UArray, assocs)

sieve :: Int -> [Int]
sieve n = [i | (i, True) <- assocs isPrime]
  where
    isPrime :: UArray Int Bool
    isPrime = runSTUArray $ do
      arr <- newArray (2, n) True
      forM_ [2 .. n] $ \p -> do
        prime <- readArray arr p
        when (prime && p * p <= n) $
          forM_ [p * p, p * p + p .. n] $ \k -> writeArray arr k False
      return arr

main :: IO ()
main = putStrLn $ "Primes up to 50: " ++ unwords (map show (sieve 50))
