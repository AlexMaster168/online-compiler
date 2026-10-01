-- Поиск в глубину: множество посещённых протягиваем через свёртку foldl.
import qualified Data.Map as Map
import qualified Data.Set as Set

graph :: Map.Map Int [Int]
graph = Map.fromList [(0, [1, 2]), (1, [0, 3]), (2, [0, 4]), (3, [1, 5]), (4, [2, 5]), (5, [3, 4])]

dfs :: Int -> (Set.Set Int, [Int]) -> (Set.Set Int, [Int])
dfs v (visited, order)
  | Set.member v visited = (visited, order)
  | otherwise = foldl (flip dfs) (Set.insert v visited, v : order) (graph Map.! v)

main :: IO ()
main = putStrLn $ "DFS order: " ++ unwords (map show (reverse (snd (dfs 0 (Set.empty, [])))))
