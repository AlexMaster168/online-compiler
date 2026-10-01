; Ханойские башни: hanoi(n, source, spare, target). Пять push-ей сохраняют регистры и выравнивают
; стек на 16 байт — без этого printf внутри рекурсии может упасть.
        default rel
        global  main
        extern  printf

        section .data
moves:    dq    0
fmt_move: db    "Move disk %ld from %c to %c", 10, 0
fmt_tot:  db    "Total moves: %ld", 10, 0

        section .text
main:
        push    rbx
        mov     edi, 3
        mov     esi, 'A'
        mov     edx, 'B'
        mov     ecx, 'C'
        call    hanoi
        lea     rdi, [fmt_tot]
        mov     rsi, [moves]
        xor     eax, eax
        call    printf wrt ..plt
        pop     rbx
        xor     eax, eax
        ret

hanoi:                                  ; rdi = n, rsi = source, rdx = spare, rcx = target
        test    rdi, rdi
        jz      .ret
        push    rbp
        push    rbx
        push    r12
        push    r13
        push    r14
        mov     rbx, rdi
        mov     r12, rsi
        mov     r13, rdx
        mov     r14, rcx
        lea     rdi, [rbx - 1]          ; n-1 дисков: source -> spare
        mov     rsi, r12
        mov     rdx, r14
        mov     rcx, r13
        call    hanoi
        lea     rdi, [fmt_move]
        mov     rsi, rbx
        mov     rdx, r12
        mov     rcx, r14
        xor     eax, eax
        call    printf wrt ..plt
        inc     qword [moves]
        lea     rdi, [rbx - 1]          ; n-1 дисков: spare -> target
        mov     rsi, r13
        mov     rdx, r12
        mov     rcx, r14
        call    hanoi
        pop     r14
        pop     r13
        pop     r12
        pop     rbx
        pop     rbp
.ret:
        ret

        section .note.GNU-stack noalloc noexec nowrite progbits
