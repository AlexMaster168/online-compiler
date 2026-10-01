; НОД по Евклиду: инструкция div кладёт частное в rax, остаток — в rdx.
        default rel
        global  main
        extern  printf

        section .data
fmt_gcd: db     "GCD(48, 18) = %ld", 10, 0
fmt_lcm: db     "LCM(48, 18) = %ld", 10, 0

        section .text
main:
        push    rbx
        mov     edi, 48
        mov     esi, 18
        call    gcd
        mov     rbx, rax                ; НОД понадобится и для НОК
        lea     rdi, [fmt_gcd]
        mov     rsi, rbx
        xor     eax, eax
        call    printf wrt ..plt
        mov     eax, 48                 ; НОК = 48 / НОД * 18
        xor     edx, edx
        div     rbx
        imul    rax, rax, 18
        lea     rdi, [fmt_lcm]
        mov     rsi, rax
        xor     eax, eax
        call    printf wrt ..plt
        pop     rbx
        xor     eax, eax
        ret

gcd:                                    ; rdi = a, rsi = b -> rax
        mov     rax, rdi
.loop:
        test    rsi, rsi
        jz      .done
        xor     edx, edx
        div     rsi                     ; rdx = a mod b
        mov     rax, rsi
        mov     rsi, rdx
        jmp     .loop
.done:
        ret

        section .note.GNU-stack noalloc noexec nowrite progbits
