-- Бинарный поиск: O(log n) на массиве Data.Array (у списков нет быстрого доступа по индексу).
import Data.Array

binarySearch :: Array Int Int -> Int -> Maybe Int
binarySearch arr target = go lo hi
  where
    (lo, hi) = bounds arr
    go l h
      | l > h = Nothing
      | arr ! mid == target = Just mid
      | arr ! mid < target = go (mid + 1) h
      | otherwise = go l (mid - 1)
      where
        mid = (l + h) `div` 2

main :: IO ()
main = do
  let values = [1, 3, 5, 7, 9, 11, 13, 15, 17, 19]
      arr = listArray (0, length values - 1) values
  mapM_ (report arr) [7, 4]
  where
    report arr target = putStrLn $ case binarySearch arr target of
      Just i -> "Found " ++ show target ++ " at index " ++ show i
      Nothing -> show target ++ " not found"
