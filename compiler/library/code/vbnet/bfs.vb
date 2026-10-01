' Поиск в ширину: Queue(Of Integer), O(V + E).
Imports System.Collections.Generic

Module Program
    Sub Main()
        Dim graph As Integer()() = {New Integer() {1, 2}, New Integer() {0, 3}, New Integer() {0, 4},
                                    New Integer() {1, 5}, New Integer() {2, 5}, New Integer() {3, 4}}
        Dim dist(graph.Length - 1) As Integer
        For i As Integer = 0 To dist.Length - 1
            dist(i) = -1
        Next
        Dim order As New List(Of Integer)
        Dim queue As New Queue(Of Integer)
        dist(0) = 0
        queue.Enqueue(0)
        While queue.Count > 0
            Dim v As Integer = queue.Dequeue()
            order.Add(v)
            For Each u As Integer In graph(v)
                If dist(u) = -1 Then
                    dist(u) = dist(v) + 1
                    queue.Enqueue(u)
                End If
            Next
        End While
        Console.WriteLine("BFS order: " & String.Join(" ", order))
        Console.WriteLine("Distances: " & String.Join(" ", dist))
    End Sub
End Module
