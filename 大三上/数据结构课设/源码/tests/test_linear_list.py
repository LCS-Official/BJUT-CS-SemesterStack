import unittest
# 从你的 models 包中导入需要测试的类
from structures.linear_list import SequentialList, LinkedList

class TestSequentialList(unittest.TestCase):
    """
    顺序表的测试
    """

    def setUp(self):
        """
        这个方法会在每个测试用例运行前被调用，
        确保每个测试都从一个干净的列表开始。
        """
        self.list = SequentialList()

    def test_initial_state(self):
        """测试顺序表的初始状态"""
        self.assertEqual(self.list.get_length(), 0)
        self.assertEqual(self.list.get_all_elements(), [])

    def test_insert(self):
        """测试插入操作"""
        self.assertTrue(self.list.insert(0, 10))  # 在空列表中插入
        self.assertEqual(self.list.get_all_elements(), [10])

        self.assertTrue(self.list.insert(0, 5))   # 在头部插入
        self.assertEqual(self.list.get_all_elements(), [5, 10])

        self.assertTrue(self.list.insert(2, 20))  # 在尾部插入
        self.assertEqual(self.list.get_all_elements(), [5, 10, 20])

        self.assertTrue(self.list.insert(1, 8))   # 在中间插入
        self.assertEqual(self.list.get_all_elements(), [5, 8, 10, 20])
        self.assertEqual(self.list.get_length(), 4)

    def test_insert_out_of_bounds(self):
        """测试插入操作的边界条件"""
        self.assertFalse(self.list.insert(-1, 10)) # 测试负数索引
        self.assertFalse(self.list.insert(1, 10))  # 测试在空列表中插入到索引1
        self.list.insert(0, 10)
        self.assertFalse(self.list.insert(2, 20))  # 测试索引越界

    def test_delete(self):
        """测试删除操作"""
        self.list.insert(0, 10)
        self.list.insert(1, 20)
        self.list.insert(2, 30)

        self.assertTrue(self.list.delete(1))  # 删除中间元素
        self.assertEqual(self.list.get_all_elements(), [10, 30])
        self.assertEqual(self.list.get_length(), 2)
        
        self.assertTrue(self.list.delete(0))  # 删除头部元素
        self.assertEqual(self.list.get_all_elements(), [30])

        self.assertTrue(self.list.delete(0))  # 删除最后一个元素
        self.assertEqual(self.list.get_all_elements(), [])
        self.assertEqual(self.list.get_length(), 0)

    def test_delete_out_of_bounds(self):
        """测试删除操作的边界条件"""
        self.assertFalse(self.list.delete(0)) # 测试在空列表中删除
        self.list.insert(0, 10)
        self.assertFalse(self.list.delete(-1))
        self.assertFalse(self.list.delete(1)) # 测试索引越界


class TestLinkedList(unittest.TestCase):
    """
    链表(LinkedList)的单元测试
    """
    def setUp(self):
        """
        确保每个测试都从一个干净的链表开始
        """
        self.list = LinkedList()

    def test_initial_state(self):
        """测试链表的初始状态"""
        self.assertEqual(self.list.get_length(), 0)
        self.assertEqual(self.list.get_all_elements(), [])

    def test_insert(self):
        """测试插入操作"""
        self.assertTrue(self.list.insert(0, 10))  # 在空链表中插入
        self.assertEqual(self.list.get_all_elements(), [10])

        self.assertTrue(self.list.insert(0, 5))   # 在头部插入
        self.assertEqual(self.list.get_all_elements(), [5, 10])

        self.assertTrue(self.list.insert(2, 20))  # 在尾部插入
        self.assertEqual(self.list.get_all_elements(), [5, 10, 20])

        self.assertTrue(self.list.insert(1, 8))   # 在中间插入
        self.assertEqual(self.list.get_all_elements(), [5, 8, 10, 20])
        self.assertEqual(self.list.get_length(), 4)
    
    def test_insert_out_of_bounds(self):
        """测试插入操作的边界条件"""
        self.assertFalse(self.list.insert(-1, 10)) # 测试负数索引
        self.assertFalse(self.list.insert(1, 10))  # 测试在空链表中插入到索引1
        self.list.insert(0, 10)
        self.assertFalse(self.list.insert(2, 20))  # 测试索引越界

    def test_delete(self):
        """测试删除操作"""
        self.list.insert(0, 10)
        self.list.insert(1, 20)
        self.list.insert(2, 30) # 链表: 10 -> 20 -> 30

        self.assertTrue(self.list.delete(1))  # 删除中间节点 (20)
        self.assertEqual(self.list.get_all_elements(), [10, 30])
        self.assertEqual(self.list.get_length(), 2)

        self.assertTrue(self.list.delete(0))  # 删除头节点 (10)
        self.assertEqual(self.list.get_all_elements(), [30])

        self.assertTrue(self.list.delete(0))  # 删除最后一个节点 (30)
        self.assertEqual(self.list.get_all_elements(), [])
        self.assertEqual(self.list.get_length(), 0)

    def test_delete_out_of_bounds(self):
        """测试删除操作的边界条件"""
        self.assertFalse(self.list.delete(0)) # 测试在空链表中删除
        self.list.insert(0, 10)
        self.assertFalse(self.list.delete(-1)) # 测试负数索引
        self.assertFalse(self.list.delete(1))  # 测试索引越界


# 这使得测试文件可以直接被运行
if __name__ == '__main__':
    unittest.main()