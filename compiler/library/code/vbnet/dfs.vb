' Поиск в глубину рекурсией: O(V + E).
Imports System.Collections.Generic

Module Program
    ReadOnly Graph As Integer()() = {New Integer() {1, 2}, New Integer() {0, 3}, New Integer() {0, 4},
                                     New Integer() {1, 5}, New Integer() {2, 5}, New Integer() {3, 4}}
    ReadOnly Visited As New HashSet(Of Integer)
    ReadOnly Order As New List(Of Integer)

    Sub Dfs(v As Integer)
        Visited.Add(v)
        Order.Add(v)
        For Each u As Integer In Graph(v)
            If Not Visited.Contains(u) Then Dfs(u)
        Next
    End Sub

    Sub Main()
        Dfs(0)
        Console.WriteLine("DFS order: " & String.Join(" ", Order))
    End Sub
End Module
