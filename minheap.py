class MinHeap:
    """Binary min-heap written by hand so the O(log k) cost is visible."""

    def __init__(self):
        self.items = []

    def __len__(self):
        return len(self.items)

    def push(self, node):
        self.items.append(node)
        i = len(self.items) - 1
        while i > 0:
            parent = (i - 1) // 2
            if self.items[i].key() < self.items[parent].key():
                self.items[i], self.items[parent] = self.items[parent], self.items[i]
                i = parent
            else:
                break

    def pop(self):
        if not self.items:
            raise IndexError("pop from empty heap")
        top = self.items[0]
        last = self.items.pop()
        if self.items:
            self.items[0] = last
            i = 0
            n = len(self.items)
            while True:
                smallest = i
                left = 2 * i + 1
                right = left + 1
                if left < n and self.items[left].key() < self.items[smallest].key():
                    smallest = left
                if right < n and self.items[right].key() < self.items[smallest].key():
                    smallest = right
                if smallest == i:
                    break
                self.items[i], self.items[smallest] = self.items[smallest], self.items[i]
                i = smallest
        return top
