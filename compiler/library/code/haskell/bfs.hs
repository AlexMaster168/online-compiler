-- Поиск в ширину: очередь — список, расстояния — Data.Map. O(V + E) (по модулю log от Map).
import qualified Data.Map as Map

graph :: Map.Map Int [Int]
graph = Map.fromList [(0, [1, 2]), (1, [0, 3]), (2, [0, 4]), (3, [1, 5]), (4, [2, 5]), (5, [3, 4])]

bfs :: Int -> ([Int], Map.Map Int Int)
bfs start = go [start] (Map.singleton start 0) []
  where
    go [] dist order = (reverse order, dist)
    go (v : queue) dist order = go (queue ++ new) dist' (v : order)
      where
        new = [u | u <- graph Map.! v, not (Map.member u dist)]
        dist' = foldr (\u -> Map.insert u (dist Map.! v + 1)) dist new

main :: IO ()
main = do
  let (order, dist) = bfs 0
  putStrLn $ "BFS order: " ++ unwords (map show order)
  putStrLn $ "Distances: " ++ unwords (map show (Map.elems dist))
