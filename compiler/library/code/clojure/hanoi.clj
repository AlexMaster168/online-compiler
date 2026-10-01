;; Ханойские башни: функция возвращает последовательность ходов, печать — отдельно.
(defn hanoi [n source spare target]
  (if (zero? n)
    []
    (concat (hanoi (dec n) source target spare)
            [[n source target]]
            (hanoi (dec n) spare source target))))

(let [moves (hanoi 3 "A" "B" "C")]
  (doseq [[n from to] moves]
    (println (str "Move disk " n " from " from " to " to)))
  (println (str "Total moves: " (count moves))))
