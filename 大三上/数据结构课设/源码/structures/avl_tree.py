# structures/avl_tree.py

class AVLNode:
    """
    AVL树的节点类
    相比BST节点，增加了height属性。
    """
    def __init__(self, key):
        self.key = key
        self.left = None
        self.right = None
        self.height = 1

    def __repr__(self):
        return f"AVLNode({self.key}, h={self.height})"

class AVLTree:
    """
    AVL树类
    """
    def __init__(self):
        self.root = None

    def _get_height(self, node):
        """获取一个节点的高度，如果节点不存在则返回0"""
        if not node:
            return 0
        return node.height

    def _get_balance(self, node):
        """计算节点的平衡因子（左 - 右）"""
        if not node:
            return 0
        return self._get_height(node.left) - self._get_height(node.right)

    def _right_rotate(self, z):
        """解决LL情况，左子树太高，右旋"""
        y = z.left
        T3 = y.right

        # 执行旋转，z扭到y的右边
        y.right = z
        z.left = T3

        # 更新高度，旋转之后，z 变成了 y 的子节点，y 的新高度依赖于 z 的新高度
        # 所以先更新z、再更新y
        z.height = 1 + max(self._get_height(z.left), self._get_height(z.right))
        y.height = 1 + max(self._get_height(y.left), self._get_height(y.right))

        return y # 返回新根

    def _left_rotate(self, z):
        """解决RR情况，右子树太高，左旋"""
        y = z.right
        T2 = y.left

        # 执行旋转，z扭到y的左边
        y.left = z
        z.right = T2

        # 更新高度
        z.height = 1 + max(self._get_height(z.left), self._get_height(z.right))
        y.height = 1 + max(self._get_height(y.left), self._get_height(y.right))

        return y
    
    def _get_min_value_node(self, node):
        """找到子树中的最小键值节点"""
        if node is None or node.left is None:
            return node
        return self._get_min_value_node(node.left)

    def insert(self, key):
        """向AVL树中插入一个新键值"""
        self.rotation_info = {"type": None, "node": None, "balance": 0, "message": ""}
        self.root = self._insert_recursive(self.root, key)

    def _insert_recursive(self, node, key):
        # 执行标准的BST插入
        if not node:
            return AVLNode(key)
        elif key < node.key:
            node.left = self._insert_recursive(node.left, key)
        elif key > node.key:
            node.right = self._insert_recursive(node.right, key)
        else:
            return node # 不允许重复键

        # 更新祖先节点的高度
        node.height = 1 + max(self._get_height(node.left), self._get_height(node.right))

        # 获取平衡因子并检查是否需要旋转
        balance = self._get_balance(node)

        # 根据四种情况执行旋转
        # LL Case
        if balance > 1 and key < node.left.key:
            self.rotation_info = {
                "type": "LL",
                "node": node,
                "balance": balance,
                "message": f"节点{node.key}的平衡因子为{balance} > 1，且新节点{key}插入在左子树的左边，执行右旋转"
            }
            return self._right_rotate(node)

        # RR Case
        if balance < -1 and key > node.right.key:
            self.rotation_info = {
                "type": "RR",
                "node": node,
                "balance": balance,
                "message": f"节点{node.key}的平衡因子为{balance} < -1，且新节点{key}插入在右子树的右边，执行左旋转"
            }
            return self._left_rotate(node)

        # LR Case，先预选转变成LL，再执行右旋
        if balance > 1 and key > node.left.key:
            self.rotation_info = {
                "type": "LR",
                "node": node,
                "balance": balance,
                "message": f"节点{node.key}的平衡因子为{balance} > 1，且新节点{key}插入在左子树的右边，先对左子树执行左旋转，再对根执行右旋转"
            }
            node.left = self._left_rotate(node.left)
            return self._right_rotate(node)

        # RL Case，先变成RR，再执行左旋
        if balance < -1 and key < node.right.key:
            self.rotation_info = {
                "type": "RL",
                "node": node,
                "balance": balance,
                "message": f"节点{node.key}的平衡因子为{balance} < -1，且新节点{key}插入在右子树的左边，先对右子树执行右旋转，再对根执行左旋转"
            }
            node.right = self._right_rotate(node.right)
            return self._left_rotate(node)

        return node

    def delete(self, key):
        """从AVL树中删除一个键值"""
        self.root = self._delete_recursive(self.root, key)

    def _delete_recursive(self, node, key):
        # 执行标准的BST删除
        if not node:
            return node
        
        if key < node.key:
            node.left = self._delete_recursive(node.left, key)
        elif key > node.key:
            node.right = self._delete_recursive(node.right, key)
        else:
            # 找到了要删除的节点
            if node.left is None:
                return node.right
            elif node.right is None:
                return node.left
            
            temp = self._get_min_value_node(node.right)
            node.key = temp.key
            node.right = self._delete_recursive(node.right, temp.key)

        if node is None:
            return node

        # 更新高度
        node.height = 1 + max(self._get_height(node.left), self._get_height(node.right))

        # 获取平衡因子并进行旋转
        balance = self._get_balance(node)

        # LL Case
        if balance > 1 and self._get_balance(node.left) >= 0:
            return self._right_rotate(node)
        
        # RR
        if balance < -1 and self._get_balance(node.right) <= 0:
            return self._left_rotate(node)

        # LR
        if balance > 1 and self._get_balance(node.left) < 0:
            node.left = self._left_rotate(node.left)
            return self._right_rotate(node)
        
        # RL
        if balance < -1 and self._get_balance(node.right) > 0:
            node.right = self._right_rotate(node.right)
            return self._left_rotate(node)

        return node

    # 存取结果
    def get_inorder_traversal(self):
        result = []
        self._inorder_recursive(self.root, result)
        return result

    #私有辅助方法，递归用
    # 中序遍历
    def _inorder_recursive(self, node, result):
        if node:
            self._inorder_recursive(node.left, result)
            result.append(node.key)
            self._inorder_recursive(node.right, result)