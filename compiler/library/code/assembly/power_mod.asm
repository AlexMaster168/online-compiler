; Быстрое возведение в степень. mul даёт 128-битное произведение в rdx:rax, div — остаток в rdx,
; поэтому переполнения нет даже без отдельного умножения по модулю.
        default rel
        global  main
        extern  printf

MOD     equ     1000000007

        section .data
fmt:    db      "%ld^%ld mod %ld = %ld", 10, 0

        section .text
main:
        push    rbx
        mov     edi, 2
        mov     esi, 30
        call    report
        mov     edi, 3
        mov     esi, 200
        call    report
        pop     rbx
        xor     eax, eax
        ret

report:                                 ; rdi = base, rsi = exp
        push    rbx
        push    r12
        push    r13
        mov     rbx, rdi
        mov     r12, rsi
        mov     edx, MOD
        call    power_mod
        lea     rdi, [fmt]
        mov     rsi, rbx
        mov     rdx, r12
        mov     ecx, MOD
        mov     r8, rax
        xor     eax, eax
        call    printf wrt ..plt
        pop     r13
        pop     r12
        pop     rbx
        ret

power_mod:                              ; rdi = base, rsi = exp, rdx = mod -> rax
        mov     r8, rdx
        mov     rax, rdi
        xor     edx, edx
        div     r8
        mov     r9, rdx                 ; base %= mod
        mov     r10, 1                  ; result
        mov     r11, rsi                ; exp
.loop:
        test    r11, r11
        jz      .done
        test    r11, 1
        jz      .square
        mov     rax, r10
        mul     r9
        div     r8
        mov     r10, rdx                ; result = result * base % mod
.square:
        mov     rax, r9
        mul     r9
        div     r8
        mov     r9, rdx                 ; base = base * base % mod
        shr     r11, 1
        jmp     .loop
.done:
        mov     rax, r10
        ret

        section .note.GNU-stack noalloc noexec nowrite progbits
