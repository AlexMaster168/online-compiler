;; Дейкстра за O(V^2): рекурсия по шагам; расстояния — map, Long/MAX_VALUE — «бесконечность».
(require '[clojure.string :as str])

(def graph {0 [[1 4] [2 1]], 1 [[3 1]], 2 [[1 2] [3 5]], 3 [[4 3]], 4 []})

(defn dijkstra [start]
  (loop [dist (assoc (zipmap (keys graph) (repeat Long/MAX_VALUE)) start 0)
         pending (set (keys graph))]
    (let [reachable (filter #(< (dist %) Long/MAX_VALUE) pending)]
      (if (empty? reachable)
        dist
        (let [v (apply min-key dist reachable)
              relaxed (reduce (fn [d [u w]] (update d u min (+ (dist v) w))) dist (graph v))]
          (recur relaxed (disj pending v)))))))

(let [dist (dijkstra 0)]
  (println (str "Dijkstra from 0: " (str/join " " (map dist (range 5))))))
