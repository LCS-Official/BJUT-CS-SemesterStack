import unittest
from structures.avl_tree import AVLTree

class TestAVLTree(unittest.TestCase):
    """
    AVL树 (AVLTree) 的单元测试
    """
    def setUp(self):
        self.avl = AVLTree()

    def test_insert_and_inorder(self):
        keys = [10, 20, 30, 40, 50, 25]
        for key in keys:
            self.avl.insert(key)
        
        expected_inorder = [10, 20, 25, 30, 40, 50]
        self.assertEqual(self.avl.get_inorder_traversal(), expected_inorder)

    def test_rr_rotation(self):
        """测试RR情况 (左旋)"""
        self.avl.insert(10)
        self.avl.insert(20)
        self.avl.insert(30) # 插入30后触发RR旋转
        
        # 旋转后，根应为20
        self.assertEqual(self.avl.root.key, 20)
        self.assertEqual(self.avl.root.left.key, 10)
        self.assertEqual(self.avl.root.right.key, 30)

    def test_ll_rotation(self):
        """测试LL情况 (右旋)"""
        self.avl.insert(30)
        self.avl.insert(20)
        self.avl.insert(10) # 插入10后触发LL旋转
        
        # 旋转后，根应为20
        self.assertEqual(self.avl.root.key, 20)
        self.assertEqual(self.avl.root.left.key, 10)
        self.assertEqual(self.avl.root.right.key, 30)

    def test_lr_rotation(self):
        """测试LR情况 (先左旋后右旋)"""
        self.avl.insert(30)
        self.avl.insert(10)
        self.avl.insert(20) # 插入20后触发LR旋转
        
        # 旋转后，根应为20
        self.assertEqual(self.avl.root.key, 20)
        self.assertEqual(self.avl.root.left.key, 10)
        self.assertEqual(self.avl.root.right.key, 30)
    
    def test_rl_rotation(self):
        """测试RL情况 (先右旋后左旋)"""
        self.avl.insert(10)
        self.avl.insert(30)
        self.avl.insert(20) # 插入20后触发RL旋转

        # 旋转后，根应为20
        self.assertEqual(self.avl.root.key, 20)
        self.assertEqual(self.avl.root.left.key, 10)
        self.assertEqual(self.avl.root.right.key, 30)

    def test_delete(self):
        """测试删除和随后的重新平衡"""
        keys = [9, 5, 10, 0, 6, 11, -1, 1, 2]
        for key in keys:
            self.avl.insert(key)
        
        # 初始树是平衡的，根是9
        self.assertEqual(self.avl.root.key, 9)
        
        # 删除10，这会使树在右侧失衡，并触发旋转
        self.avl.delete(10)
        
        # 验证删除后的有序性
        expected_inorder = [-1, 0, 1, 2, 5, 6, 9, 11]
        self.assertEqual(self.avl.get_inorder_traversal(), expected_inorder)
        
        # 验证删除并旋转后树依然是平衡的，根节点可能已经改变
        # 在这个特定例子中，删除10后，根节点会变成1
        self.assertEqual(self.avl.root.key, 1)

# 使得测试文件可以直接被运行
if __name__ == '__main__':
    unittest.main()