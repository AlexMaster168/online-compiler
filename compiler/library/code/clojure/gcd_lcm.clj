;; НОД по Евклиду: recur — хвостовой вызов самой функции.
(defn gcd [a b]
  (if (zero? b) a (recur b (mod a b))))

(defn lcm [a b]
  (* (quot a (gcd a b)) b))

(println (str "GCD(48, 18) = " (gcd 48 18)))
(println (str "LCM(48, 18) = " (lcm 48 18)))
