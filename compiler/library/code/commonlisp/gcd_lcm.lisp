;;; НОД по Евклиду. (В Common Lisp есть встроенные gcd/lcm — пишем свои.)
(defun my-gcd (a b)
  (if (zerop b) a (my-gcd b (mod a b))))

(defun my-lcm (a b)
  (* (floor a (my-gcd a b)) b))

(format t "GCD(48, 18) = ~a~%" (my-gcd 48 18))
(format t "LCM(48, 18) = ~a~%" (my-lcm 48 18))
