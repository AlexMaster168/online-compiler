; Поиск в глубину рекурсией: visit(v) отмечает вершину, дописывает её в order и обходит соседей.
        default rel
        global  main
        extern  printf

V       equ     6

        section .data
adj:    dq      1, 2,  0, 3,  0, 4,  1, 5,  2, 5,  3, 4
count:  dq      0
label:  db      "DFS order:", 0
fmt_s:  db      "%s", 0
fmt_n:  db      " %ld", 0
fmt_nl: db      10, 0

        section .bss
visited: resb   V
order:   resq   V

        section .text
main:
        push    rbx
        xor     edi, edi
        call    visit
        lea     rdi, [label]
        lea     rsi, [order]
        mov     rdx, [count]
        call    print_list
        pop     rbx
        xor     eax, eax
        ret

visit:                                  ; rdi = v
        push    rbx
        push    r12
        push    r13
        mov     rbx, rdi
        lea     rax, [visited]
        mov     byte [rax + rbx], 1
        lea     rax, [order]
        mov     rcx, [count]
        mov     [rax + rcx*8], rbx
        inc     qword [count]
        xor     r12d, r12d              ; k — номер соседа
.loop:
        cmp     r12, 2
        jge     .done
        lea     rax, [adj]
        lea     rcx, [rbx*2 + r12]
        mov     r13, [rax + rcx*8]      ; u
        lea     rax, [visited]
        cmp     byte [rax + r13], 0
        jne     .next
        mov     rdi, r13
        call    visit
.next:
        inc     r12
        jmp     .loop
.done:
        pop     r13
        pop     r12
        pop     rbx
        ret

print_list:
        push    rbx
        push    r12
        push    r13
        mov     rbx, rsi
        mov     r12, rdx
        xor     r13d, r13d
        mov     rsi, rdi
        lea     rdi, [fmt_s]
        xor     eax, eax
        call    printf wrt ..plt
.loop:
        cmp     r13, r12
        jge     .end
        lea     rdi, [fmt_n]
        mov     rsi, [rbx + r13*8]
        xor     eax, eax
        call    printf wrt ..plt
        inc     r13
        jmp     .loop
.end:
        lea     rdi, [fmt_nl]
        xor     eax, eax
        call    printf wrt ..plt
        pop     r13
        pop     r12
        pop     rbx
        ret

        section .note.GNU-stack noalloc noexec nowrite progbits
