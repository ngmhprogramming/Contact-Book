#Stack class from Half PS 2

class Stack:
    def __init__(self):
        self._top=None
        self._size = 0
    class StackNode:
        def __init__(self, item, link):
            self.item= item
            self.next = link
    def empty(self):
        return self._top is None
    def __len__(self):
        return self._size
    def top(self):
        return self._top.item
    def pop(self):
        self._top = self._top.next
        self._size -= 1
    def push(self, item):
        self._top = self.StackNode(item, self._top)
        self._size += 1