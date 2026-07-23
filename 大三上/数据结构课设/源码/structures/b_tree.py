class BTreeNode:
    def __init__(self, t, leaf=False):
        self.t = t
        self.keys = []
        self.children = []
        self.leaf = leaf

    def is_full(self):
        return len(self.keys) >= 2 * self.t - 1


class BTree:
    def __init__(self, t=3):
        if t < 2:
            raise ValueError("B-tree minimum degree must be at least 2")
        self.t = t
        self.root = None

    def search(self, node, key):
        if node is None:
            return None
        i = 0
        while i < len(node.keys) and key > node.keys[i]:
            i += 1
        if i < len(node.keys) and node.keys[i] == key:
            return (node, i)
        if node.leaf:
            return None
        return self.search(node.children[i], key)

    def split_child(self, parent, index):
        """
        分裂子节点
        """
        t = self.t
        y = parent.children[index]
        z = BTreeNode(t, leaf=y.leaf)

        up_key = y.keys[t - 1]

        z.keys = y.keys[t:]

        y.keys = y.keys[:t - 1]

        if not y.leaf:
            z.children = y.children[t:]
            y.children = y.children[:t]

        parent.children.insert(index + 1, z)
        parent.keys.insert(index, up_key)

    def insert(self, key):
        if self.root is None:
            self.root = BTreeNode(self.t, leaf=True)
            self.root.keys = [key]
            return

        if self.root.is_full():
            s = BTreeNode(self.t, leaf=False)
            s.children.append(self.root)
            self.split_child(s, 0)
            # 决定用哪个子节点继续插入
            i = 0
            if s.keys and key > s.keys[0]:
                i = 1
            self._insert_non_full(s.children[i], key)
            self.root = s
        else:
            self._insert_non_full(self.root, key)

    def _insert_non_full(self, node, key):
        i = len(node.keys) - 1
        if node.leaf:
            # 插入到叶子节点
            node.keys.append(None)
            while i >= 0 and key < node.keys[i]:
                node.keys[i + 1] = node.keys[i]
                i -= 1
            node.keys[i + 1] = key
        else:
            # 插入到非叶子节点
            while i >= 0 and key < node.keys[i]:
                i -= 1
            i += 1
            # 如果子节点已满，先分裂
            if node.children[i].is_full():
                self.split_child(node, i)
                if key > node.keys[i]:
                    i += 1
            self._insert_non_full(node.children[i], key)

    def get_all_elements(self):
        """
        以中序遍历的方式获取B树中的所有关键字，返回一个列表
        """
        res = []

        def traverse(n):
            if n is None:
                return
            for i, k in enumerate(n.keys):
                if not n.leaf:
                    traverse(n.children[i])
                res.append(k)
            if not n.leaf:
                traverse(n.children[len(n.keys)])

        traverse(self.root)
        return res

    def get_length(self):
        """
        递归计算B树中所有关键字的总数
        """
        if self.root is None:
            return 0

        def _count_keys(node):
            # 获取当前节点的关键字数量
            count = len(node.keys)
            # 如果不是叶子节点，累加所有子节点的关键字数量
            if not node.leaf:
                for child in node.children:
                    count += _count_keys(child)
            return count

        return _count_keys(self.root)

    def __repr__(self):
        return f"BTree(t={self.t}, root_keys={self.root.keys if self.root else None})\n"