#AVLTree class from PS4

class AVLTreeNode:
    def __init__(self, key, values=[]):
        #O(1)
        #Create variables needed for each node
        self.key = key
        self.values = values
        if type(values) != list: self.values = [self.values]
        self.left = None
        self.right = None
        self.height = 1

class AVLTree:
    def insert(self, root, key, value):
        #O(log n)
        #Normal BST insertion
        if root is None:
            return AVLTreeNode(key, value)
        elif key < root.key:
            root.left = self.insert(root.left, key, value)
        elif key > root.key:
            root.right = self.insert(root.right, key, value)
        else:
            root.values.insert(0, value)

        #Update height
        root.height = 1+max(self.height(root.left), self.height(root.right))

        #Check balance
        balance = self.balance(root)

        #Rotate if needed
        #Left-Left
        if balance > 1 and key < root.left.key:
            return self.rRotate(root)
 
        #Right Right
        if balance < -1 and key > root.right.key:
            return self.lRotate(root)
 
        #Left Right
        if balance > 1 and key > root.left.key:
            root.left = self.lRotate(root.left)
            return self.rRotate(root)
 
        #Right Left
        if balance < -1 and key < root.right.key:
            root.right = self.rRotate(root.right)
            return self.lRotate(root)
        return root
    def inside(self, root, key, value):
        #O(log n)
        #Normal BST search
        #Checks if node is present
        if root is None:
            return False
        elif key == root.key:
            return value in root.values
        elif key < root.key:
            return self.inside(root.left, key, value)
        else:
            return self.inside(root.right, key, value)
    def search(self, root, key):
        #O(log n)
        #Normal BST search
        #Returns all nodes present with same key
        if root is None:
            return None
        elif key == root.key:
            return root
        elif key < root.key:
            return self.search(root.left, key)
        else:
            return self.search(root.right, key)
    def lessThan(self, root, high, equal):
        #O(n)
        #Normal BST search
        #Returns all nodes with key less than input
        #With equal if flagged
        if root is None:
            return []
        r = []
        if root.left is not None:
            r += self.lessThan(root.left, high, equal)
        if root.key < high or (equal and root.key == high):
            r.append(root)
        if root.right is not None:
            r += self.lessThan(root.right, high, equal)
        return r
    def greaterThan(self, root, low, equal):
        #O(n)
        #Normal BST search
        #Returns all nodes with key greater than input
        #With equal if flagged
        if root is None:
            return []
        r = []
        if root.left is not None:
            r += self.greaterThan(root.left, low, equal)
        if root.key > low or (equal and root.key == low):
            r.append(root)
        if root.right is not None:
            r += self.greaterThan(root.right, low, equal)
        return r
    def inRange(self, root, low, high, equal1, equal2):
        #O(n)
        #Normal BST search
        #Returns all nodes with key less than input and greater than input
        #With equal if flagged
        if root is None:
            return []
        r = []
        if root.left is not None:
            r += self.inRange(root.left, low, high, equal1, equal2)
        if root.key < high and root.key > low or (equal2 and root.key == high) or (equal1 and root.key == low):
            r.append(root)
        if root.right is not None:
            r += self.inRange(root.right, low, high, equal1, equal2)
        return r
    def all(self, root):
        #O(n)
        #Normal BST search
        #Returns all nodes
        if root is None:
            return []
        r = []
        if root.left is not None:
            r += self.all(root.left)
        r.append(root)
        if root.right is not None:
            r += self.all(root.right)
        return r
    def delete(self, root, key, value):
        #O(log n)
        #Normal BST Delete
        if root is None:
            return root
        elif key < root.key:
            root.left = self.delete(root.left, key, value)
        elif key > root.key:
            root.right = self.delete(root.right, key, value)
        else:
            if value is not None:
                if len(root.values) > 1:
                    root.values.remove(value)
                    return root
                elif root.values[0] != value:
                    return root 
            if root.left is None:
                temp = root.right
                root = None
                return temp
            elif root.right is None:
                temp = root.left
                root = None
                return temp
            temp = self.minimum(root.right)
            root.key = temp.key
            root.values = temp.values
            root.right = self.delete(root.right, temp.key,value)

        #If it is gone
        if root is None:
            return root

        #Update Height
        root.height = 1+max(self.height(root.left), self.height(root.right))


        #Check balance
        balance = self.balance(root)

        #Rotate if needed
        #Left-Left
        if balance > 1 and self.balance(root.left) >= 0:
            return self.rRotate(root)
 
        #Right Right
        if balance < -1 and self.balance(root.right) <= 0:
            return self.lRotate(root)
 
        #Left Right
        if balance > 1 and self.balance(root.left) < 0:
            root.left = self.lRotate(root.left)
            return self.rRotate(root)
 
        #Right Left
        if balance < -1 and self.balance(root.right) > 0:
            root.right = self.rRotate(root.right)
            return self.lRotate(root)
        return root
    def height(self, root):
        #O(1)
        #Returns height of subtree rooted at root
        #If it's not a tree it doesn't have a height
        #Else just get the height
        if root is None: return 0
        return root.height
    def balance(self, root):
        #O(1)
        #Returns balance of subtree rooted at root, which is the difference beteween the height of the 2 subtrees
        #If it's not a tree it doesn't have a balance
        #Else get the difference between height of subtrees
        if root is None: return 0;
        return self.height(root.left)-self.height(root.right)
    def lRotate(self, root):
        #O(1)
        #Temporary Storage
        r = root.right
        rl = r.left

        #Swap Around
        r.left = root
        root.right = rl

        #Update Heights
        root.height = 1+max(self.height(root.left), self.height(root.right))
        r.height = 1+max(self.height(r.left), self.height(r.right))
        return r
    def rRotate(self, root):
        #O(1)
        #Temporary Storage
        l = root.left
        lr = l.right

        #Swap Around
        l.right = root
        root.left = lr
        
        #Update Heights
        root.height = 1+max(self.height(root.left), self.height(root.right))
        l.height = 1+max(self.height(l.left), self.height(l.right))
        return l
    def minimum(self, root):
        #O(log n)
        #Leftmost node in tree
        #If we reach the end just return
        #Else continue going left
        if root is None or root.left is None: return root
        return self.minimum(root.left)
    def maximum(self, root):
        #O(log n)
        #Rightmost node in tree
        #If we reach the end just return
        #Else continue going left
        if root is None or root.right is None: return root
        return self.maximum(root.right)
    def __str__(self, root):
        #O(n)
        #Return string representation of node
        #If it isn't a node represent it as a blank
        #Else return the left child, itself, and the right child
        if root is None: return "(-)"
        return "("+self.string(root.left)+str(root.key)+self.string(root.right)+")"
    __repr__ = __str__
