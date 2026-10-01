; Решето Эратосфена: composite — байт на число (0 — простое), печатаем сразу, как нашли простое.
        default rel
        global  main
        extern  printf

N       equ     50

        section .data
label:  db      "Primes up to 50:", 0
fmt_n:  db      " %ld", 0
fmt_nl: db      10, 0

        section .bss
composite: resb N + 1

        section .text
main:
        push    rbx
        push    r12
        push    r13
        lea     rdi, [label]
        xor     eax, eax
        call    printf wrt ..plt
        lea     r12, [composite]
        mov     rbx, 2                  ; p
.each:
        cmp     rbx, N
        jg      .done
        cmp     byte [r12 + rbx], 0
        jne     .next
        lea     rdi, [fmt_n]
        mov     rsi, rbx
        xor     eax, eax
        call    printf wrt ..plt
        mov     r13, rbx
        imul    r13, rbx                ; k = p * p
.cross:
        cmp     r13, N
        jg      .next
        mov     byte [r12 + r13], 1
        add     r13, rbx
        jmp     .cross
.next:
        inc     rbx
        jmp     .each
.done:
        lea     rdi, [fmt_nl]
        xor     eax, eax
        call    printf wrt ..plt
        pop     r13
        pop     r12
        pop     rbx
        xor     eax, eax
        ret

        section .note.GNU-stack noalloc noexec nowrite progbits
