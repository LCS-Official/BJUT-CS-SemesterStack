import unittest
from structures.binary_tree import BinarySearchTree

class TestBinarySearchTree(unittest.TestCase):
    """
    二叉搜索树 (BinarySearchTree) 的单元测试
    """
    def setUp(self):
        """
        在每个测试用例运行前，构建一个固定的BST。
        结构如下:
              15
             /  \
            6    18
           / \   / \
          3   7 17  20
         / \   \
        2   4   13
        """
        self.bst = BinarySearchTree()
        keys = [15, 6, 18, 3, 7, 17, 20, 2, 4, 13]
        for key in keys:
            self.bst.insert(key)

    def test_insert_and_inorder_traversal(self):
        """测试插入和中序遍历"""
        # BST的中序遍历结果应该是一个有序列表
        expected = [2, 3, 4, 6, 7, 13, 15, 17, 18, 20]
        self.assertEqual(self.bst.get_inorder_traversal(), expected)

    def test_search(self):
        """测试查找操作"""
        # 测试存在的节点
        self.assertIsNotNone(self.bst.search(15)) # root
        self.assertIsNotNone(self.bst.search(2))  # leaf
        self.assertIsNotNone(self.bst.search(7))  # middle
        
        # 测试不存在的节点
        self.assertIsNone(self.bst.search(99))
        self.assertIsNone(self.bst.search(1))
    
    def test_delete_leaf_node(self):
        """测试删除叶子节点 (情况1)"""
        self.bst.delete(2) # 删除叶子节点 2
        expected = [3, 4, 6, 7, 13, 15, 17, 18, 20]
        self.assertEqual(self.bst.get_inorder_traversal(), expected)
        self.assertIsNone(self.bst.search(2))

        self.bst.delete(17) # 删除叶子节点 17
        expected = [3, 4, 6, 7, 13, 15, 18, 20]
        self.assertEqual(self.bst.get_inorder_traversal(), expected)
        self.assertIsNone(self.bst.search(17))

    def test_delete_node_with_one_child(self):
        """测试删除只有一个子节点的节点 (情况2)"""
        self.bst.delete(7) # 删除节点 7 (它有一个右子节点 13)
        expected = [2, 3, 4, 6, 13, 15, 17, 18, 20]
        self.assertEqual(self.bst.get_inorder_traversal(), expected)
        self.assertIsNone(self.bst.search(7))
        # 验证原子节点6的右子节点现在是13
        node_6 = self.bst.search(6)
        self.assertEqual(node_6.right.key, 13)

    def test_delete_node_with_two_children(self):
        """测试删除有两个子节点的节点 (情况3)"""
        self.bst.delete(6) # 删除节点 6 (它有两个子节点 3 和 7)
        # 6会被它的中序后继 7 替换
        expected = [2, 3, 4, 7, 13, 15, 17, 18, 20]
        self.assertEqual(self.bst.get_inorder_traversal(), expected)
        self.assertIsNone(self.bst.search(6))
        # 验证原子节点7现在的位置
        self.assertEqual(self.bst.search(15).left.key, 7)

    def test_delete_root_node(self):
        """测试删除根节点"""
        self.bst.delete(15) # 删除根节点 15
        # 15会被它的中序后继 17 替换
        expected = [2, 3, 4, 6, 7, 13, 17, 18, 20]
        self.assertEqual(self.bst.get_inorder_traversal(), expected)
        self.assertIsNone(self.bst.search(15))
        # 验证新根节点是17
        self.assertEqual(self.bst.root.key, 17)


# 使得测试文件可以直接被运行
if __name__ == '__main__':
    unittest.main()