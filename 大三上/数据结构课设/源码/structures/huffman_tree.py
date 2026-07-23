# structrues/huffman_tree.py
import heapq

class HuffmanNode:
    """
    哈夫曼树节点类
    """
    def __init__(self, weight, char=None, left=None, right=None):
        self.weight = weight  # 权重
        self.char = char      # 叶子的字符
        self.left = left      # 左子节点
        self.right = right    # 右子节点

    def __lt__(self, other):
        """
        比较方法，用于让优先队列heapq能够根据节点的权重进行排序（隐式自动调用）
        """
        return self.weight < other.weight
    
    def __repr__(self):
        """
        格式化表示
        """
        return f"Node(w={self.weight}, char='{self.char}')"


class HuffmanTree:
    """
    哈夫曼树类
    """
    def __init__(self):
        """
        初始化一个空哈夫曼树对象
        """
        self.root = None
        self._codes = {} # halfman编码

    def build_from_frequencies(self, frequencies: dict):
        """
        立刻构建哈夫曼树，利用下面分步构建的函数
        """
        step_generator = self.build_step_by_step(frequencies)
        for state in step_generator:
            self.root = state.get("tree") # 持续更新树根
        return self.root

    def build_step_by_step(self, frequencies: dict):
        """
        分步构建哈夫曼树的生成器
        每一步yield一个状态字典
        """
        if not frequencies:
            self.root = None
            yield {"queue": [], "tree": None, "text": "错误：频率数据为空。"}
            return

        # 初始化优先队列
        priority_queue = []
        for char, weight in frequencies.items():
            node = HuffmanNode(weight=weight, char=char)
            heapq.heappush(priority_queue, node)
        
        # 初始状态：显示所有叶子节点
        yield {
            "queue": list(priority_queue), 
            "tree": None, 
            "text": "1. 初始化优先队列，包含所有叶子节点。"
        }

        # 循环构建
        step = 2
        while len(priority_queue) > 1:
            # 弹出前
            yield {
                "queue": list(priority_queue), 
                "tree": None, 
                "highlight_nodes": heapq.nsmallest(2, priority_queue),
                "text": f"{step}. 从队列中选择权重最小的两个节点。"
            }
            step += 1 # display步数（到第几步了）

            # 弹出两个最小的节点
            left_node = heapq.heappop(priority_queue)
            right_node = heapq.heappop(priority_queue)

            # 创建新父节点
            merged_weight = left_node.weight + right_node.weight
            merged_node = HuffmanNode(weight=merged_weight, left=left_node, right=right_node)
            
            yield {
                "queue": list(priority_queue), 
                "merged_tree": merged_node, # 新合并的子树
                "text": f"{step}. 合并节点 '{left_node.char or left_node.weight}' 和 '{right_node.char or right_node.weight}'\n"
                        f"   创建权重为 {merged_weight} 的新父节点。"
            }
            step += 1

            # 将新节点放回队列
            heapq.heappush(priority_queue, merged_node)
            yield {
                "queue": list(priority_queue), 
                "tree": None,
                "highlight_nodes": [merged_node],
                "text": f"{step}. 将新的父节点放回优先队列。"
            }
            step += 1

        # 完成
        self.root = priority_queue[0] if priority_queue else None
        yield {
            "queue": [], 
            "tree": self.root, 
            "text": "构建完成！"
        }

    def generate_codes(self):
        """
        生成并返回每个字符的哈夫曼编码
        """
        if self.root is None:
            return {}
        
        # 清空旧的编码，从根节点开始递归生成
        self._codes = {}
        self._generate_codes_recursive(self.root, "")
        return self._codes

    def _generate_codes_recursive(self, node, current_code):
        """
        私有，用于遍历树并生成编码
        """
        if node is None:
            return

        # 如果是叶子节点，则记录其编码
        if node.char is not None:
            self._codes[node.char] = current_code
            return

        # 往左走，编码加'0'
        self._generate_codes_recursive(node.left, current_code + "0")
        # 往右走，编码加'1'
        self._generate_codes_recursive(node.right, current_code + "1")