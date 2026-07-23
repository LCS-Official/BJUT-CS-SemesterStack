# structures/binary_tree.py

# 树节点，普通、BST共用
class TreeNode:
    def __init__(self, key):
        self.key = key
        self.left = None
        self.right = None
    def __repr__(self):
        return f"TreeNode({self.key})" #可视化

# BST类
class BinarySearchTree:
    def __init__(self):
        self.root = None

    def insert(self, key):
        if self.root is None:
            self.root = TreeNode(key) #如果没根，插入在根的地方
        else:
            self._insert_recursive(self.root, key) # 进入递归
    
    def _insert_recursive(self, node, key): # 递归插入，比较左右子节点，决定往左还是往右走
        if key < node.key:
            if node.left is None:
                node.left = TreeNode(key)
            else:
                self._insert_recursive(node.left, key)
        elif key > node.key:
            if node.right is None:
                node.right = TreeNode(key)
            else:
                self._insert_recursive(node.right, key)
    
    def search(self, key):
        return self._search_recursive(self.root, key) # 进入查找
    
    def _search_recursive(self, node, key): # 递归查找
        if node is None or node.key == key:
            return node
        if key < node.key:
            return self._search_recursive(node.left, key)
        else:
            return self._search_recursive(node.right, key)
    
    def delete(self, key):
        self.root = self._delete_recursive(self.root, key) # 进入删除
    
    def _delete_recursive(self, node, key): # 递归删除，选择往左往右递归，返回删除后的子树根节点
        if node is None:
            return node
        if key < node.key:
            node.left = self._delete_recursive(node.left, key) 
        elif key > node.key:
            node.right = self._delete_recursive(node.right, key)
        else:
            if node.left is None:
                return node.right
            elif node.right is None:
                return node.left
            min_larger_node = self._get_min_value_node(node.right) # 在有两个子节点时，根不能直接删掉，需要找到右子树的最小节点来替换
            node.key = min_larger_node.key
            node.right = self._delete_recursive(node.right, min_larger_node.key)
        return node
    
    def _get_min_value_node(self, node): # 找到以node为根的子树的最小节点
        current = node
        while current.left is not None: #不断往左走就能找到最小节点
            current = current.left
        return current
    
    def get_inorder_traversal(self): # 中序遍历，返回一个列表
        result = []
        self._inorder_recursive(self.root, result)
        return result

    def _inorder_recursive(self, node, result): # 递归中序遍历
        if node:
            self._inorder_recursive(node.left, result)
            result.append(node.key)
            self._inorder_recursive(node.right, result)
    
    def search_path(self, key):
        """
        为可视化提供路径，返回一个生成器（路径表示）
        """
        node = self.root
        while node is not None:
            yield node # 高亮该节点
            if key < node.key:
                node = node.left
            elif key > node.key:
                node = node.right
            else:
                yield node # 再次高亮，重复出现则找到
                return

    def delete_path(self, key):
        """
        分步演示删除节点过程，每一步都 yield 一个包含当前树状态和解释文本的字典
        将BST的标准删除操作分解成一步一步的可视化帧
        """
        path_stack = []  # 记录路径
        node = self.root
        parent = None
        is_left = None

        if node:
            yield {"tree": self.root, "highlight_node": node, "text": f"开始查找节点: {key}，从根节点 {node.key} 开始"}

        # 查找要删除的节点
        while node and node.key != key:
            path_stack.append((parent, node, is_left))
            parent = node
            if key < node.key:
                node = node.left
                is_left = True
            else:
                node = node.right
                is_left = False
            yield {"tree": self.root, "highlight_node": node, "text": f"查找节点: {key}，当前节点: {getattr(node, 'key', None)}"}
        
        if node is None:
            yield {"tree": self.root, "highlight_node": None, "text": f"未找到节点 {key}，无法删除。"}
            return
        
        # 删除节点，分类讨论
        # 若只有一个子节点或无子节点
        def replace_parent(parent, node, new_child, is_left):
            if parent is None:
                self.root = new_child
            else:
                if is_left:
                    parent.left = new_child
                else:
                    parent.right = new_child

        # 若为叶子节点或单子节点
        if node.left is None or node.right is None:
            new_child = node.left if node.left else node.right
            replace_parent(parent, node, new_child, is_left)
            yield {"tree": self.root, "highlight_node": node, "text": f"删除节点 {key}，直接替换为其唯一子节点或None。"}
            return
        
        # 若有两个子节点，找右子树最小节点（公式化操作）
        min_parent = node
        min_node = node.right
        min_is_left = False
        while min_node.left:
            min_parent = min_node
            min_node = min_node.left
            min_is_left = True
            yield {"tree": self.root, "highlight_node": min_node, "text": f"寻找右子树最小节点: 当前 {min_node.key}"}
        # 交换值
        old_key = node.key
        node.key = min_node.key
        yield {"tree": self.root, "highlight_node": node, "text": f"用右子树最小节点 {min_node.key} 替换被删节点 {old_key}"}
        # 删除最小节点
        if min_is_left:
            min_parent.left = min_node.right
        else:
            min_parent.right = min_node.right
        yield {"tree": self.root, "highlight_node": min_node, "text": f"删除右子树最小节点 {min_node.key}"}
        yield {"tree": self.root, "highlight_node": None, "text": f"节点 {old_key} 已被删除，过程结束。"}
        return


# 普通二叉树类
class GenericBinaryTree:
    def __init__(self):
        self.root = None

    def build_from_pre_in(self, preorder: list, inorder: list):
        ''' 
        分步构建二叉树，从前序和中序遍历结果构建
        不断压栈，先压左孩子，再压右孩子。其中递归压左子、右子。先记录根在哪儿
        逐步 yield 当前树状态和解释文本
        '''
        if not preorder or not inorder:
            self.root = None
            yield {"tree": self.root, "info": {}}
            return

        inorder_map = {val: i for i, val in enumerate(inorder)} # 快速获得中序序列里面根的索引（它左边、右边是谁？）
        pre_idx_ref = [0] # 前序序列中，应该追踪的下一个根节点索引（下一个创建谁？）

        # 使用栈模拟递归过程，从而让我们能在节点连接后 yield
        self.root = None
        stack = []
        
        # 第一步 处理根节点
        root_val = preorder[pre_idx_ref[0]] # preorder[0] 永远是当前树（或子树）的根

        self.root = TreeNode(root_val) # 创建根节点实例
        pre_idx_ref[0] += 1 # 下一个根节点索引前移，指向下一个
        
        in_index = inorder_map[root_val] # 在中序序列中找到根的位置
        info = { 
            "highlight_node": self.root, 
            "text": f"开始构建:\n"
                    f"  - 前序: {preorder}\n"
                    f"  - 中序: {inorder}\n"
                    f"根是 '{root_val}'"
        }
        yield {"tree": self.root, "info": info} # 找到根了！是root_val
        
        # 将右子树和左子树的构建任务依次压栈（先右后左，这样左子树会先被处理）
        if in_index + 1 <= len(inorder) - 1:
            stack.append((self.root, 'right', in_index + 1, len(inorder) - 1))
        if 0 <= in_index - 1:
            stack.append((self.root, 'left', 0, in_index - 1))


        # 第二步 迭代处理栈中的任务
        while stack:
            parent, direction, in_start, in_end = stack.pop() # 栈里面存储的是任务，包括父节点、是左还是右子树、当前中序子问题的起止索引
            
            root_val = preorder[pre_idx_ref[0]] # 当前子问题的根节点（创建新节点）
            node = TreeNode(root_val)
            pre_idx_ref[0] += 1

            # 先连接，再yield，在可视化之前连接好节点
            if direction == 'left':
                parent.left = node
            else:
                parent.right = node

            # 找到根在中序序列中的索引，方便后续可视化
            in_index = inorder_map[root_val]

            # 优化显示信息 
            preorder_slice_start = pre_idx_ref[0] - 1
            subproblem_len = in_end - in_start + 1
            current_preorder_slice = preorder[preorder_slice_start : preorder_slice_start + subproblem_len]
            current_inorder_slice = inorder[in_start : in_end + 1]
            info = { 
                "highlight_node": node, 
                "text": f"处理子问题:\n"
                        f"  - 前序: {current_preorder_slice}\n"
                        f"  - 中序: {current_inorder_slice}\n"
                        f"根是 '{root_val}'"
            }
            yield {"tree": self.root, "info": info}
            
            # 再次将子任务压栈（分配新任务）
            if in_index + 1 <= in_end:
                stack.append((node, 'right', in_index + 1, in_end))
            if in_start <= in_index - 1:
                stack.append((node, 'left', in_start, in_index - 1))

        yield {"tree": self.root, "info": {"text": "构建完成！"}}




    def build_from_post_in(self, postorder: list, inorder: list):
        ''' 
        分步构建二叉树，从后序和中序遍历结果构建
        不断压栈，先压左孩子，再压右孩子。其中递归压左子、右子。先记录根在哪儿
        逐步 yield 当前树状态和解释文本
        '''
        if not postorder or not inorder:
            self.root = None
            yield {"tree": self.root, "info": {}}
            return

        inorder_map = {val: i for i, val in enumerate(inorder)}
        post_idx_ref = [len(postorder) - 1] # 后序序列中，应该追踪的下一个根节点索引
        
        # 同样使用迭代的方式来重构
        self.root = None
        stack = []

        # 处理根节点
        root_val = postorder[post_idx_ref[0]]
        self.root = TreeNode(root_val)
        post_idx_ref[0] -= 1
        
        in_index = inorder_map[root_val]
        info = { 
            "highlight_node": self.root, 
            "text": f"开始构建:\n"
                    f"  - 后序: {postorder}\n"
                    f"  - 中序: {inorder}\n"
                    f"根是 '{root_val}'"
        }
        yield {"tree": self.root, "info": info}
        
        # 后序是左右根，所以构建时倒过来是根右左
        if 0 <= in_index - 1:
            stack.append((self.root, 'left', 0, in_index - 1))
        if in_index + 1 <= len(inorder) - 1:
            stack.append((self.root, 'right', in_index + 1, len(inorder) - 1))
            
        while stack:
            parent, direction, in_start, in_end = stack.pop()
            
            root_val = postorder[post_idx_ref[0]]
            node = TreeNode(root_val)
            post_idx_ref[0] -= 1
            
            if direction == 'left':
                parent.left = node
            else:
                parent.right = node
            
            in_index = inorder_map[root_val]
            
            # 优化显示信息
            subproblem_len = in_end - in_start + 1
            postorder_slice_end = post_idx_ref[0] + 1
            current_postorder_slice = postorder[postorder_slice_end - subproblem_len : postorder_slice_end]
            current_inorder_slice = inorder[in_start : in_end + 1]
            info = { 
                "highlight_node": node, 
                "text": f"处理子问题:\n"
                        f"  - 后序: {current_postorder_slice}\n"
                        f"  - 中序: {current_inorder_slice}\n"
                        f"根是 '{root_val}'"
            }
            yield {"tree": self.root, "info": info}
            
            if in_start <= in_index - 1:
                stack.append((node, 'left', in_start, in_index - 1))
            if in_index + 1 <= in_end:
                stack.append((node, 'right', in_index + 1, in_end))

        yield {"tree": self.root, "info": {"text": "构建完成！"}}
    


    def build_from_level_order(self, level_order: list):
        '''
        分步构建二叉树，从层序遍历结果构建
        用deque来模拟层序遍历的队列行为
        逐步 yield 当前树状态和解释文本
        '''
        from collections import deque # 使用双端队列方便弹出和添加节点
        if not level_order or level_order[0] is None:
            self.root = None
            yield {"tree": self.root, "info": {}}
            return
        
        nodes_iter = iter(level_order)
        self.root = TreeNode(next(nodes_iter))
        queue = deque([self.root]) # 队列存放已经建好的树节点
        
        yield { "tree": self.root, "info": {"highlight_node": self.root, "text": f"创建根节点: {self.root.key}"} }

        while queue:
            current_node = queue.popleft()
            try:
                left_val = next(nodes_iter)
                if left_val is not None:
                    current_node.left = TreeNode(left_val)
                    queue.append(current_node.left)
                    yield { "tree": self.root, "info": {"highlight_node": current_node.left, "text": f"节点 {current_node.key} 创建左孩子: {left_val}"} }

                right_val = next(nodes_iter)
                if right_val is not None:
                    current_node.right = TreeNode(right_val)
                    queue.append(current_node.right)
                    yield { "tree": self.root, "info": {"highlight_node": current_node.right, "text": f"节点 {current_node.key} 创建右孩子: {right_val}"} }
            except StopIteration:
                break
        
        yield {"tree": self.root, "info": {"text": "构建完成！"}}