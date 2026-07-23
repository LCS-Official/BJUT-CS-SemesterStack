# structures/linear_list.py

# Part 1: 顺序表
class SequentialList:
    """
    顺序表类
    用list实现
    """
    def __init__(self):
        """
        初始化
        """
        self._elements = []

    def __repr__(self):
        """
        提供顺序表的字符串表示
        """
        return f"SequentialList({self._elements})"

    def insert(self, index: int, value):
        """
        在指定索引位置插入一个元素
        """
        # 检查是否越界
        if index < 0 or index > len(self._elements):
            return False
        self._elements.insert(index, value)
        return True

    def delete(self, index: int):
        """
        删除指定索引位置的元素
        """
        if index < 0 or index >= len(self._elements):
            return False
        self._elements.pop(index)
        return True

    def get_all_elements(self):
        """
        返回包含所有元素的列表，方便绘制
        """
        return self._elements.copy()

    def get_length(self):
        """
        返回顺序表的长度
        """
        return len(self._elements)
    



# Part 2: Linked List
class LinkedList:
    """
    单链表类
    """
    class _Node:
        """
        内部节点类，表示链表的节点
        """
        def __init__(self, value, next_node=None):
            self.value = value
            self.next = next_node

    def __init__(self):
        """
        初始化一个空的链表
        """
        self._head = None

    def __repr__(self):
        """
        可视化
        """
        if self._head is None:
            return "LinkedList(None)"
        
        current = self._head
        nodes_str = []
        while current:
            nodes_str.append(str(current.value))
            current = current.next
        return f"LinkedList({' -> '.join(nodes_str)} -> None)" # 格式化表示

    def insert(self, index: int, value):
        """
        在指定索引位置插入一个新节点
        """
        if index < 0:
            return False

        new_node = self._Node(value) #实例一个新节点
        
        if index == 0:
            # 头插
            new_node.next = self._head
            self._head = new_node
            return True

        # 找到要插入位置的前一个节点
        current = self._head
        for _ in range(index - 1):
            if current is None: # index 超出范围
                return False
            current = current.next
        
        if current is None: # index 超出范围
            return False
            
        # 执行插入
        new_node.next = current.next
        current.next = new_node
        return True

    def delete(self, index: int):
        """
        删除指定索引位置的节点
        """
        if self._head is None or index < 0:
            return False

        if index == 0:
            # 删除头节点
            self._head = self._head.next
            return True

        # 找到要删除位置的前一个节点
        current = self._head
        for _ in range(index - 1):
            if current.next is None: # index 超出范围
                return False
            current = current.next

        if current.next is None:
            return False

        # 执行删除
        current.next = current.next.next # 处理“指针”
        return True

    def get_all_elements(self):
        """
        返回包含所有节点值的列表，方便绘制
        """
        elements = []
        current = self._head
        while current:
            elements.append(current.value)
            current = current.next
        return elements

    def get_length(self):
        """
        返回链表的长度
        """
        count = 0
        current = self._head
        while current:
            count += 1
            current = current.next #遍历一遍链表
        return count