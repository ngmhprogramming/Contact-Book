#Graph model
#How I wish this was done in C++

from csv import DictReader

class Connectivity:
    def __init__(self):
        self.source = ""
        self.end = ""
        #Stored as an adjacency list, mapping each node to the other nodes it connects
        self.edges = {}
        self.visited = []
    #Read in graph
    #A global adjacency list is used
    #To prevent excessively long lookup by checking every single book
    def read(self):
        edges = {}
        with open("graph.gr", "r") as file:
            r = DictReader(file)
            for i in r:
                if i["source"] in edges.keys(): edges[i["source"]].append(i["end"])
                else: edges[i["source"]] = [i["end"]]
        self.edges = edges
    #Perform Depth First Search to get minimum distance
    #O(N)
    def dfs(self, node, dist, path):
        #Do not visit node again, as it is never optimal
        if node in self.visited: return -1, []
        self.visited.append(node)
        if node == self.end: return dist, path
        best = -1
        route = []
        #Node has out-degree 0
        if node not in self.edges.keys():
            return -1, []
        for i in self.edges[node]:
            #Continue traversal
            t, u = self.dfs(i, dist+1, path+[i])
            #Save minimum route
            if t != -1:
                if best == -1 or best < t:
                    best = t
                    route = u
        return best, route
    #Perform Depth First Search to get minimum distance
    #Avoid using the owner's contacts
    #O(N)
    def dfs_ex(self, avoid, node, dist, path):
        #Do not visit node again, as it is never optimal
        if node in self.visited: return -1, []
        self.visited.append(node)
        if node == self.end: return dist, path
        best = -1
        route = []
        #Node has out-degree 0
        if node not in self.edges.keys():
            return -1, []
        for i in self.edges[node]:
            #Continue traversal
            #Do not continue if we are forbidden
            #We are not forbidden if we are the destination
            if i == avoid and avoid == self.end:
                return dist+1, path+[i]
            if i != avoid:
                t, u = self.dfs_ex(avoid, i, dist+1, path+[i])
                #Save minimum route
                if t != -1:
                    if best == -1 or best < t:
                        best = t
                        route = u
        return best, route
    #Get distance and path information
    def path(self, source, end, avoid):
        self.source = source
        self.end = end
        self.visited = []
        r1, s1 = self.dfs(self.source, 0, [self.source])
        self.visited = []
        r2, s2 = self.dfs_ex(avoid, self.source, 0, [self.source])
        self.visited = []
        r = [[r1, s1], [r2, s2]]
        return r