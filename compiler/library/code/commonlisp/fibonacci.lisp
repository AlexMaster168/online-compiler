;;; Числа Фибоначчи: loop с параллельным присваиванием (psetf). Целые безразмерные.
(defun fib (n)
  (let ((a 0) (b 1))
    (dotimes (i n a)
      (psetf a b
             b (+ a b)))))

(format t "Fibonacci: ~{~a~^ ~}~%" (loop for i below 15 collect (fib i)))
(format t "F(50) = ~a~%" (fib 50))
