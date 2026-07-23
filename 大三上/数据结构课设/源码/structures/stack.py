# structures/stack.py

class SequentialStack:
    """
    顺序栈类
    用list实现
    """
    def __init__(self):
        """
        初始化空栈
        """
        self._elements = []

    def __repr__(self):
        """
        提供栈的字符串表示
        """
        # 栈顶元素在列表的末尾，反转列表以正确显示
        top_first_list = reversed(self._elements)
        return f"SequentialStack(top -> {list(top_first_list)})"

    def push(self, value):
        """
        将一个元素压入栈顶
        """
        self._elements.append(value)

    def pop(self):
        """
        从栈顶弹出一个元素
        """
        if self.is_empty():
            return None
        return self._elements.pop()

    def top(self):
        """
        查看栈顶元素
        """
        if self.is_empty():
            return None
        return self._elements[-1] # 负索引，获取最后一个元素

    def is_empty(self):
        """
        检查栈是否为空
        """
        return len(self._elements) == 0

    def get_length(self):
        """
        返回栈中元素的数量
        """
        return len(self._elements)
    
    def get_all_elements(self):
        """
        返回包含所有元素的列表，方便View层进行绘制
        """
        return self._elements.copy()