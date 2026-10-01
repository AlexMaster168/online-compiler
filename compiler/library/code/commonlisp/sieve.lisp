;;; Решето Эратосфена на битовом векторе: 1 — число вычеркнуто.
(defun sieve (n)
  (let ((composite (make-array (1+ n) :element-type 'bit :initial-element 0)))
    (loop for p from 2 to n
          when (zerop (bit composite p))
            collect p
            and do (loop for k from (* p p) to n by p
                         do (setf (bit composite k) 1)))))

(format t "Primes up to 50: ~{~a~^ ~}~%" (sieve 50))
