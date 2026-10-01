;;; Факториал рекурсией. Числа в Lisp растут сами — переполнения нет.
(defun factorial (n)
  (if (<= n 1) 1 (* n (factorial (1- n)))))

(format t "10! = ~a~%" (factorial 10))
(format t "20! = ~a~%" (factorial 20))
