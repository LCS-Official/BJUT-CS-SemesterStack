import unittest
from structures.huffman_tree import HuffmanTree

class TestHuffmanTree(unittest.TestCase):
    """
    哈夫曼树(HuffmanTree)的单元测试
    """
    def test_huffman_construction_and_codes(self):
        """
        测试一个标准的哈夫曼树构建和编码生成过程。
        使用维基百科上的经典例子。
        """
        frequencies = {
            'a': 45, 'b': 13, 'c': 12, 'd': 16, 'e': 9, 'f': 5
        }
        
        h_tree = HuffmanTree(frequencies)
        
        # 1. 根节点的权重应该是所有频率之和
        self.assertIsNotNone(h_tree.root)
        self.assertEqual(h_tree.root.weight, 100)

        # 2. 生成哈夫曼编码
        codes = h_tree.generate_codes()

        # 3. 验证编码是否正确 (这是该频率下的一种可能的最优编码)
        expected_codes = {
            'a': '0',
            'b': '101',
            'c': '100',
            'd': '111',
            'e': '1101',
            'f': '1100'
        }
        self.assertDictEqual(codes, expected_codes)

        # 4. 验证编码是否满足前缀码性质
        code_list = list(codes.values())
        for i in range(len(code_list)):
            for j in range(i + 1, len(code_list)):
                self.assertFalse(code_list[i].startswith(code_list[j]))
                self.assertFalse(code_list[j].startswith(code_list[i]))

    def test_empty_input(self):
        """测试输入为空字典的情况"""
        h_tree = HuffmanTree({})
        self.assertIsNone(h_tree.root)
        self.assertDictEqual(h_tree.generate_codes(), {})

    def test_single_char_input(self):
        """测试输入只有一个字符的情况"""
        h_tree = HuffmanTree({'a': 10})
        self.assertEqual(h_tree.root.weight, 10)
        self.assertEqual(h_tree.root.char, 'a')
        
        # 对于单个字符，编码可以是空的或'0'，这取决于实现。
        # 一个更鲁棒的实现可能会给它一个'0'，但空字符串也合理。
        codes = h_tree.generate_codes()
        self.assertIn(codes['a'], ["", "0"]) # 接受 "" 或 "0"

# 使得测试文件可以直接被运行
if __name__ == '__main__':
    unittest.main()