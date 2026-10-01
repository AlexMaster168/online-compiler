*> Сортировка пузырьком: O(n^2). Таблицы COBOL (OCCURS) индексируются с 1.
*> Исходные данные задаём строкой цифр, которая «накладывается» на таблицу.
IDENTIFICATION DIVISION.
PROGRAM-ID. BUBBLE-SORT.
DATA DIVISION.
WORKING-STORAGE SECTION.
01 WS-DATA VALUE "050209010506".
   05 WS-A PIC 99 OCCURS 6 TIMES.
01 WS-N       PIC 9(4) VALUE 6.
01 WS-I       PIC 9(4).
01 WS-J       PIC 9(4).
01 WS-TMP     PIC 99.
01 WS-SWAPPED PIC 9.
01 WS-OUT     PIC Z(17)9.
PROCEDURE DIVISION.
    PERFORM VARYING WS-I FROM 1 BY 1 UNTIL WS-I > WS-N - 1
        MOVE 0 TO WS-SWAPPED
        PERFORM VARYING WS-J FROM 1 BY 1 UNTIL WS-J > WS-N - WS-I
            IF WS-A(WS-J) > WS-A(WS-J + 1)
                MOVE WS-A(WS-J) TO WS-TMP
                MOVE WS-A(WS-J + 1) TO WS-A(WS-J)
                MOVE WS-TMP TO WS-A(WS-J + 1)
                MOVE 1 TO WS-SWAPPED
            END-IF
        END-PERFORM
        IF WS-SWAPPED = 0
            EXIT PERFORM
        END-IF
    END-PERFORM
    DISPLAY "Sorted:" WITH NO ADVANCING
    PERFORM VARYING WS-I FROM 1 BY 1 UNTIL WS-I > WS-N
        MOVE WS-A(WS-I) TO WS-OUT
        DISPLAY " " FUNCTION TRIM(WS-OUT) WITH NO ADVANCING
    END-PERFORM
    DISPLAY SPACE
    STOP RUN.
