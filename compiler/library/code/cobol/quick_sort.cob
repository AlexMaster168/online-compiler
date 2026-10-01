*> Быстрая сортировка (разбиение Ломуто) без рекурсии: отрезки [LO, HI], которые
*> осталось отсортировать, лежат в явном стеке — так быструю сортировку обычно и пишут на COBOL.
IDENTIFICATION DIVISION.
PROGRAM-ID. QUICK-SORT.
DATA DIVISION.
WORKING-STORAGE SECTION.
01 WS-DATA VALUE "10070809010503".
   05 WS-A PIC 99 OCCURS 7 TIMES.
01 WS-N      PIC 9(4) VALUE 7.
01 WS-STACK.
   05 WS-RANGE OCCURS 50 TIMES.
      10 WS-SLO PIC 9(4).
      10 WS-SHI PIC 9(4).
01 WS-TOP    PIC 9(4) VALUE 0.
01 WS-LO     PIC 9(4).
01 WS-HI     PIC 9(4).
01 WS-I      PIC 9(4).
01 WS-J      PIC 9(4).
01 WS-PIVOT  PIC 99.
01 WS-TMP    PIC 99.
01 WS-OUT    PIC Z(17)9.
PROCEDURE DIVISION.
    ADD 1 TO WS-TOP
    MOVE 1 TO WS-SLO(WS-TOP)
    MOVE WS-N TO WS-SHI(WS-TOP)
    PERFORM UNTIL WS-TOP = 0
        MOVE WS-SLO(WS-TOP) TO WS-LO
        MOVE WS-SHI(WS-TOP) TO WS-HI
        SUBTRACT 1 FROM WS-TOP
        IF WS-LO < WS-HI
            *> разбиение: всё меньше опоры — влево, опора встаёт на место WS-I
            MOVE WS-A(WS-HI) TO WS-PIVOT
            MOVE WS-LO TO WS-I
            PERFORM VARYING WS-J FROM WS-LO BY 1 UNTIL WS-J >= WS-HI
                IF WS-A(WS-J) < WS-PIVOT
                    MOVE WS-A(WS-I) TO WS-TMP
                    MOVE WS-A(WS-J) TO WS-A(WS-I)
                    MOVE WS-TMP TO WS-A(WS-J)
                    ADD 1 TO WS-I
                END-IF
            END-PERFORM
            MOVE WS-A(WS-I) TO WS-TMP
            MOVE WS-A(WS-HI) TO WS-A(WS-I)
            MOVE WS-TMP TO WS-A(WS-HI)
            IF WS-I > WS-LO
                ADD 1 TO WS-TOP
                MOVE WS-LO TO WS-SLO(WS-TOP)
                COMPUTE WS-SHI(WS-TOP) = WS-I - 1
            END-IF
            ADD 1 TO WS-TOP
            COMPUTE WS-SLO(WS-TOP) = WS-I + 1
            MOVE WS-HI TO WS-SHI(WS-TOP)
        END-IF
    END-PERFORM
    DISPLAY "Sorted:" WITH NO ADVANCING
    PERFORM VARYING WS-I FROM 1 BY 1 UNTIL WS-I > WS-N
        MOVE WS-A(WS-I) TO WS-OUT
        DISPLAY " " FUNCTION TRIM(WS-OUT) WITH NO ADVANCING
    END-PERFORM
    DISPLAY SPACE
    STOP RUN.
