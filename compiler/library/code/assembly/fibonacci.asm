; Числа Фибоначчи итеративно: пара (a, b) -> (b, a + b) в регистрах r12 и r13.
        default rel
        global  main
        extern  printf

        section .data
label:  db      "Fibonacci:", 0
fmt_n:  db      " %ld", 0
fmt_f:  db      10, "F(50) = %ld", 10, 0

        section .text
main:
        push    rbx
        push    r12
        push    r13
        lea     rdi, [label]
        xor     eax, eax
        call    printf wrt ..plt
        xor     r12d, r12d              ; a = F(0)
        mov     r13, 1                  ; b = F(1)
        xor     ebx, ebx                ; i
.loop:
        cmp     rbx, 15
        jge     .skip_print
        lea     rdi, [fmt_n]
        mov     rsi, r12
        xor     eax, eax
        call    printf wrt ..plt
.skip_print:
        cmp     rbx, 50
        je      .done
        lea     rax, [r12 + r13]
        mov     r12, r13
        mov     r13, rax
        inc     rbx
        jmp     .loop
.done:
        lea     rdi, [fmt_f]
        mov     rsi, r12
        xor     eax, eax
        call    printf wrt ..plt
        pop     r13
        pop     r12
        pop     rbx
        xor     eax, eax
        ret

        section .note.GNU-stack noalloc noexec nowrite progbits
