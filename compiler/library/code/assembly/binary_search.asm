; Бинарный поиск: binary_search(target) -> индекс в rax или -1.
        default rel
        global  main
        extern  printf

N       equ     10

        section .data
arr:      dq    1, 3, 5, 7, 9, 11, 13, 15, 17, 19
targets:  dq    7, 4
fmt_hit:  db    "Found %ld at index %ld", 10, 0
fmt_miss: db    "%ld not found", 10, 0

        section .text
main:
        push    rbx
        push    r12
        push    r13                     ; три push-а: стек выровнен для printf
        lea     r12, [targets]
        xor     r13d, r13d              ; номер цели
.each:
        cmp     r13, 2
        jge     .exit
        mov     rbx, [r12 + r13*8]      ; target
        mov     rdi, rbx
        call    binary_search
        test    rax, rax
        js      .miss
        lea     rdi, [fmt_hit]
        mov     rsi, rbx
        mov     rdx, rax
        xor     eax, eax
        call    printf wrt ..plt
        jmp     .next
.miss:
        lea     rdi, [fmt_miss]
        mov     rsi, rbx
        xor     eax, eax
        call    printf wrt ..plt
.next:
        inc     r13
        jmp     .each
.exit:
        pop     r13
        pop     r12
        pop     rbx
        xor     eax, eax
        ret

binary_search:                          ; rdi = target
        lea     r8, [arr]
        xor     ecx, ecx                ; lo
        mov     rdx, N - 1              ; hi
.loop:
        cmp     rcx, rdx
        jg      .not_found
        lea     rax, [rcx + rdx]
        sar     rax, 1                  ; mid
        mov     r9, [r8 + rax*8]
        cmp     r9, rdi
        je      .found
        jl      .go_right
        lea     rdx, [rax - 1]          ; hi = mid - 1
        jmp     .loop
.go_right:
        lea     rcx, [rax + 1]          ; lo = mid + 1
        jmp     .loop
.found:
        ret
.not_found:
        mov     rax, -1
        ret

        section .note.GNU-stack noalloc noexec nowrite progbits
