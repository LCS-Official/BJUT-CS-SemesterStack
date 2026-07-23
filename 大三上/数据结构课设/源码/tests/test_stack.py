import unittest
from structures.stack import SequentialStack

class TestSequentialStack(unittest.TestCase):
    """
    顺序栈的测试
    """
    def setUp(self):
        """
        在每个测试用例运行前，初始化一个空的栈。
        """
        self.stack = SequentialStack()

    def test_initial_state(self):
        """测试栈的初始状态"""
        self.assertTrue(self.stack.is_empty())
        self.assertEqual(self.stack.get_length(), 0)
        self.assertIsNone(self.stack.peek())

    def test_push(self):
        """测试入栈操作"""
        self.stack.push(10)
        self.assertFalse(self.stack.is_empty())
        self.assertEqual(self.stack.get_length(), 1)
        self.assertEqual(self.stack.peek(), 10)

        self.stack.push(20)
        self.assertEqual(self.stack.get_length(), 2)
        self.assertEqual(self.stack.peek(), 20) # 栈顶应该是后压入的元素

    def test_pop(self):
        """测试出栈操作"""
        self.stack.push(10)
        self.stack.push(20)
        self.stack.push(30)

        # LIFO (Last-In, First-Out) 后进先出
        self.assertEqual(self.stack.pop(), 30)
        self.assertEqual(self.stack.get_length(), 2)
        self.assertEqual(self.stack.peek(), 20)
        
        self.assertEqual(self.stack.pop(), 20)
        self.assertEqual(self.stack.get_length(), 1)
        self.assertEqual(self.stack.peek(), 10)

        self.assertEqual(self.stack.pop(), 10)
        self.assertEqual(self.stack.get_length(), 0)
        self.assertTrue(self.stack.is_empty())

    def test_pop_from_empty_stack(self):
        """测试从空栈中出栈"""
        self.assertIsNone(self.stack.pop())
        self.assertTrue(self.stack.is_empty())

    def test_get_all_elements(self):
        """测试获取所有元素的方法"""
        self.assertEqual(self.stack.get_all_elements(), [])
        self.stack.push(10)
        self.stack.push(20)
        self.stack.push(30)
        # 栈底 -> 栈顶
        self.assertEqual(self.stack.get_all_elements(), [10, 20, 30])


# 使得测试文件可以直接被运行
if __name__ == '__main__':
    unittest.main()