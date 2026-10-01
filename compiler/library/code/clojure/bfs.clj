;; Поиск в ширину: PersistentQueue — неизменяемая очередь, расстояния — map.
(require '[clojure.string :as str])

(def graph {0 [1 2], 1 [0 3], 2 [0 4], 3 [1 5], 4 [2 5], 5 [3 4]})

(defn bfs [start]
  (loop [queue (conj clojure.lang.PersistentQueue/EMPTY start)
         dist {start 0}
         order []]
    (if (empty? queue)
      [order dist]
      (let [v (peek queue)
            new (remove dist (graph v))]
        (recur (into (pop queue) new)
               (into dist (map (fn [u] [u (inc (dist v))]) new))
               (conj order v))))))

(let [[order dist] (bfs 0)]
  (println (str "BFS order: " (str/join " " order)))
  (println (str "Distances: " (str/join " " (map dist (range 6))))))
