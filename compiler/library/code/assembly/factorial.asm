; Факториал рекурсией: n сохраняется на стеке через push/pop вокруг рекурсивного вызова.
        default rel
        global  main
        extern  printf

        section .data
fmt:    db      "%ld! = %lu", 10, 0

        section .text
main:
        push    rbx
        mov     edi, 10
        call    factorial
        lea     rdi, [fmt]
        mov     esi, 10
        mov     rdx, rax
        xor     eax, eax
        call    printf wrt ..plt
        mov     edi, 20
        call    factorial
        lea     rdi, [fmt]
        mov     esi, 20
        mov     rdx, rax
        xor     eax, eax
        call    printf wrt ..plt
        pop     rbx
        xor     eax, eax
        ret

factorial:                              ; rdi = n -> rax = n!
        cmp     rdi, 1
        jg      .recurse
        mov     eax, 1
        ret
.recurse:
        push    rdi
        dec     rdi
        call    factorial
        pop     rdi
        imul    rax, rdi
        ret

        section .note.GNU-stack noalloc noexec nowrite progbits
