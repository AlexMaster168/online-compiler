;;; Быстрое возведение в степень: loop с переменными, обновляемыми на каждом шаге.
(defconstant +mod+ 1000000007)

(defun power-mod (base exp m)
  (loop with result = 1
        for b = (mod base m) then (mod (* b b) m)
        for e = exp then (ash e -1)
        while (> e 0)
        when (oddp e) do (setf result (mod (* result b) m))
        finally (return result)))

(format t "2^30 mod ~a = ~a~%" +mod+ (power-mod 2 30 +mod+))
(format t "3^200 mod ~a = ~a~%" +mod+ (power-mod 3 200 +mod+))
