;; Решето Эратосфена: множество вычеркнутых растёт через reduce.
(require '[clojure.string :as str])

(defn sieve [n]
  (let [composite (reduce (fn [crossed p]
                            (if (crossed p)
                              crossed
                              (into crossed (range (* p p) (inc n) p))))
                          #{}
                          (range 2 (inc n)))]
    (remove composite (range 2 (inc n)))))

(println (str "Primes up to 50: " (str/join " " (sieve 50))))
