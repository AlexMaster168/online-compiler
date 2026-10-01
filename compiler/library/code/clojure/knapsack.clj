;; Рюкзак 0/1: reduce по предметам строит каждую новую строку dp из предыдущей.
(defn knapsack [items capacity]
  (peek (reduce (fn [dp [w v]]
                  (mapv (fn [c] (if (>= c w) (max (dp c) (+ (dp (- c w)) v)) (dp c)))
                        (range (inc capacity))))
                (vec (repeat (inc capacity) 0))
                items)))

(println (str "Knapsack max value: " (knapsack [[1 1] [3 4] [4 5] [5 7]] 7)))
