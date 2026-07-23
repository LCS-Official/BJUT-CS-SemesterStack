# controllers/main_controller.py

import copy
import random
from collections import Counter
import copy
from structures.linear_list import SequentialList, LinkedList
from structures.stack import SequentialStack
from structures.binary_tree import BinarySearchTree, GenericBinaryTree, TreeNode
from structures.huffman_tree import HuffmanTree, HuffmanNode
from structures.b_tree import BTree
from structures.avl_tree import AVLTree, AVLNode
from PySide6.QtWidgets import QInputDialog
from PySide6.QtWidgets import QInputDialog, QFileDialog
from PySide6.QtCore import QTimer, QObject, Signal, QCoreApplication
from PySide6.QtGui import QColor
from algorithms import knapsac, infix_to_postfix, postfix_evaluation, parentheses_matching
import json
import os
try:
    from openai import OpenAI
except Exception:
    OpenAI = None
import threading

class MainController(QObject):
    # 定义一个信号，参数为 str，用于从后台线程将 AI 回复传回主线程处理
    ai_response_received = Signal(str)
    def __init__(self, view):
        super().__init__()
        # 强制禁用本地连接的代理，确保本地 LM Studio 访问不被代理拦截
        try:
            os.environ["NO_PROXY"] = "localhost,127.0.0.1"
            os.environ["no_proxy"] = "localhost,127.0.0.1"
        except Exception:
            pass

        self._view = view
        
        self._models = {
            "sequential_list": SequentialList(),
            "linked_list": LinkedList(),
            "stack": SequentialStack(),
            "bst": BinarySearchTree(),
            "avl": AVLTree(),
            "generic_tree": GenericBinaryTree(),
            "huffman_tree": None, # 哈夫曼树在使用时创建
            "b_tree": BTree(t=3)
        }
        
        self._active_model_name = "sequential_list"
        # 为查找过程添加状态变量
        self._search_path_iterator = None
        self._highlighted_node_key = None
        # 为顺序表分步查找/删除添加状态变量
        self._seq_search_iterator = None
        self._seq_search_target = None
        self._seq_search_current_index = None

        self._seq_delete_iterator = None
        self._seq_delete_target = None
        self._seq_delete_current_index = None
        # 可视化临时数组（如分步删除时的移动中间状态）
        self._seq_delete_display_array = None
        # 可视化临时数组（顺序表分步插入时的移动中间状态）
        self._seq_insert_display_array = None
        # 顺序表/链表 插入分步状态变量
        self._seq_insert_iterator = None
        self._seq_insert_index = None
        self._seq_insert_value = None
        self._seq_insert_current_index = None
        # 链表插入可视化信息（place/relink 阶段）
        self._linked_insert_info = None
        # 链表重连可视化信息（用于分步删除）
        self._linked_reconnect_info = None

        # 为构建过程添加状态变量
        self._build_iterator = None
        self._current_build_info = None

        # 为BST分步删除添加状态变量
        self._delete_path_iterator = None
        self._current_delete_info = None
        self._delete_history = [] # 保存删除历史
        self._current_delete_step = -1 # 当前步数索引

        # 为哈夫曼树分步构建添加状态变量
        self._huffman_build_iterator = None
        self._current_huffman_build_state = None
        self._huffman_build_history = [] # 保存构建历史
        self._current_huffman_build_step = -1 # 当前步数索引

        # 为AVL树添加历史记录状态变量
        self._avl_history = []  # 保存AVL树的历史状态
        self._current_avl_step = -1  # 当前在历史记录中的位置
        self._current_avl_info = None  # 当前要显示的AVL步信息
        # 自动重置的延迟（毫秒），用于在演示结束后保留最终高亮一小会儿
        self._auto_reset_delay_ms = 1500
        # 栈的临时可视化提示（用于 push/pop/top 的短暂高亮/标记）
        self._stack_viz = None

        # 背包问题演示状态
        self._knapsack_gen = None  # 生成器
        self._knapsack_items = None  # 原始物品列表
        self._knapsack_weights = None  # 权重列表
        self._knapsack_capacity = None  # 容量
        self._knapsack_stack = []  # 当前栈中的索引
        self._knapsack_remaining = None  # 剩余容量
        self._knapsack_play_timer = None  # 自动播放计时器
        self._knapsack_discarded = []  # 被丢弃的物品索引（尝试过但因容量不足被拒绝的）
        # 中缀转后缀 演示状态
        self._infix_gen = None
        self._infix_expr = None
        # 后缀求值 演示状态
        self._postfix_eval_gen = None

        self._paren_match_gen = None

        # B-树 解释文本状态
        self._current_btree_info = None

        # When True, handle_structure_change will skip clearing visuals and
        # resetting the previous model. This is used during load operations
        # to avoid race conditions where the structure-toggle handlers
        # would erase the model we just restored.
        self._suppress_structure_side_effects = False
        
        # 防止初始化期间 mode_change 信号被多次触发
        self._initializing = True

        # AI 客户端配置
        # LM Studio 默认不需要 API Key，但库要求填一个非空字符串
        try:
            if OpenAI is not None:
                self.ai_client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")
            else:
                self.ai_client = None
        except Exception as e:
            print(f"AI Client init failed: {e}")
            self.ai_client = None

        self._connect_signals()
        # 将后台 AI 回复信号连接到主线程的处理函数
        try:
            self.ai_response_received.connect(self._process_ai_response)
        except Exception:
            pass
        # 初始化演示模式的面板可见性（直接调用，不依赖信号）
        self._initializing = False
        self.handle_mode_change()

        try:
            self.handle_structure_change(self._active_model_name)
        except Exception:
            pass
        self.update_view()

    def _connect_signals(self):
        """
        连接视图中的信号到控制器的处理方法
        万物之源
        """
        # 演示模式选择
        self._view.radio_data_structure.toggled.connect(self.handle_mode_change)
        self._view.radio_algorithm.toggled.connect(self.handle_mode_change)
        # 当切换到算法演示时，根据当前子选择（背包/中缀->后缀）重置对应演示
        def _on_algo_mode_toggled(checked):
            if not checked or getattr(self, '_initializing', False):
                return
            try:
                if hasattr(self._view, 'radio_algo_infix') and self._view.radio_algo_infix.isChecked():
                    self.handle_algorithm_change('infix')
                else:
                    self.handle_algorithm_change('knapsack')
            except Exception:
                pass

        self._view.radio_algorithm.toggled.connect(_on_algo_mode_toggled)
        
        # 动态操作按钮
        self._view.insert_button.clicked.connect(self.handle_insert)
        self._view.delete_button.clicked.connect(self.handle_delete)
        
        # 分步删除按钮
        self._view.start_delete_button.clicked.connect(self.handle_delete_start)
        self._view.prev_delete_step_button.clicked.connect(self.handle_delete_prev)
        self._view.next_delete_step_button.clicked.connect(self.handle_delete_next)
        self._view.reset_delete_button.clicked.connect(self.handle_delete_reset)

        # 数据结构选择
        self._view.radio_sequential_list.toggled.connect(lambda: self.handle_structure_change("sequential_list"))
        self._view.radio_linked_list.toggled.connect(lambda: self.handle_structure_change("linked_list"))
        self._view.radio_stack.toggled.connect(lambda: self.handle_structure_change("stack"))
        self._view.radio_bst.toggled.connect(lambda: self.handle_structure_change("bst"))
        self._view.radio_avl.toggled.connect(lambda: self.handle_structure_change("avl"))
        self._view.radio_generic_tree.toggled.connect(lambda: self.handle_structure_change("generic_tree"))
        self._view.radio_huffman_tree.toggled.connect(lambda: self.handle_structure_change("huffman_tree"))
        # B-树
        if hasattr(self._view, 'radio_b_tree'):
            self._view.radio_b_tree.toggled.connect(lambda: self.handle_structure_change("b_tree"))
        
        # 查找按钮
        self._view.search_button.clicked.connect(self.handle_search_start)
        self._view.next_step_button.clicked.connect(self.handle_search_next)
        self._view.reset_button.clicked.connect(self.handle_search_reset)

        # 构建演示按钮
        self._view.start_build_button.clicked.connect(self.handle_build_start)
        self._view.next_build_step_button.clicked.connect(self.handle_build_next)
        self._view.reset_build_button.clicked.connect(self.handle_build_reset)

        # BST 构建按钮
        self._view.bst_build_button.clicked.connect(self.handle_bst_build)
        # BST 随机生成序列按钮
        if hasattr(self._view, 'bst_random_button'):
            self._view.bst_random_button.clicked.connect(self.handle_bst_random_generate)
        # BST 重置树按钮（清空整个BST）
        if hasattr(self._view, 'bst_reset_tree_button'):
            self._view.bst_reset_tree_button.clicked.connect(self.handle_bst_reset_tree)

        # 哈夫曼树构建按钮
        # 随机生成输入（a~g 的随机字母权重）
        if hasattr(self._view, 'huffman_random_button'):
            self._view.huffman_random_button.clicked.connect(self.handle_huffman_random_generate)
        self._view.huffman_draw_button.clicked.connect(self.handle_huffman_draw)
        self._view.huffman_start_button.clicked.connect(self.handle_huffman_build_start)
        self._view.huffman_prev_step_button.clicked.connect(self.handle_huffman_build_prev)
        self._view.huffman_next_step_button.clicked.connect(self.handle_huffman_build_next)
        self._view.huffman_reset_button.clicked.connect(self.handle_huffman_build_reset)

        # Knapsack algorithm run button
        if hasattr(self._view, 'knap_run_button'):
            self._view.knap_run_button.clicked.connect(self.handle_knapsack_run)
        if hasattr(self._view, 'knap_next_step_button'):
            self._view.knap_next_step_button.clicked.connect(self.handle_knapsack_step_next)
        if hasattr(self._view, 'knap_reset_button'):
            self._view.knap_reset_button.clicked.connect(self.handle_knapsack_reset)

        # Algorithm selection radios
        if hasattr(self._view, 'radio_algo_knapsack'):
            self._view.radio_algo_knapsack.toggled.connect(lambda checked: self.handle_algorithm_change('knapsack') if checked else None)
        if hasattr(self._view, 'radio_algo_infix'):
            self._view.radio_algo_infix.toggled.connect(lambda checked: self.handle_algorithm_change('infix') if checked else None)

        if hasattr(self._view, 'radio_algo_paren'):
            self._view.radio_algo_paren.toggled.connect(lambda checked: self.handle_algorithm_change('paren_match') if checked else None)
        #

        # Infix -> Postfix generator demo buttons
        if hasattr(self._view, 'infix_run_button'):
            self._view.infix_run_button.clicked.connect(self.handle_infix_run)
        if hasattr(self._view, 'infix_next_step_button'):
            self._view.infix_next_step_button.clicked.connect(self.handle_infix_step_next)
        if hasattr(self._view, 'infix_reset_button'):
            self._view.infix_reset_button.clicked.connect(self.handle_infix_reset)

        # 后缀求值 按钮连接
        if hasattr(self._view, 'postfix_eval_run_button'):
            self._view.postfix_eval_run_button.clicked.connect(self.handle_postfix_eval_run)
        if hasattr(self._view, 'postfix_eval_next_button'):
            self._view.postfix_eval_next_button.clicked.connect(self.handle_postfix_eval_next)
        if hasattr(self._view, 'postfix_eval_reset_button'):
            self._view.postfix_eval_reset_button.clicked.connect(self.handle_postfix_eval_reset)

        # B-树设置按钮
        if hasattr(self._view, 'btree_set_button'):
            self._view.btree_set_button.clicked.connect(self.handle_btree_reset_degree)

        # AI 按钮连接
        if hasattr(self._view, 'ai_send_button'):
            try:
                self._view.ai_send_button.clicked.connect(self.handle_ai_request)
                # 按回车发送
                if hasattr(self._view, 'ai_input'):
                    self._view.ai_input.returnPressed.connect(self.handle_ai_request)
            except Exception:
                pass

        # 括号匹配按钮
        if hasattr(self._view, 'paren_run_button'):
            self._view.paren_run_button.clicked.connect(self.handle_paren_match_run)
        if hasattr(self._view, 'paren_next_button'):
            self._view.paren_next_button.clicked.connect(self.handle_paren_match_next)
        if hasattr(self._view, 'paren_reset_button'):
            self._view.paren_reset_button.clicked.connect(self.handle_paren_match_reset)

        # AVL树历史操作按钮
        self._view.avl_prev_button.clicked.connect(self.handle_avl_prev)
        self._view.avl_next_button.clicked.connect(self.handle_avl_next)
        self._view.avl_history_reset_button.clicked.connect(self.handle_avl_history_reset)
        # GenericBinaryTree 随机生成序列按钮（前序+中序 / 后序+中序 / 层序）
        if hasattr(self._view, 'pre_in_random_button'):
            self._view.pre_in_random_button.clicked.connect(self.handle_pre_in_random)
        if hasattr(self._view, 'post_in_random_button'):
            self._view.post_in_random_button.clicked.connect(self.handle_post_in_random)
        if hasattr(self._view, 'level_random_button'):
            self._view.level_random_button.clicked.connect(self.handle_level_random)
        # 顺序表分步查找/删除按钮
        if hasattr(self._view, 'seq_search_start'):
            self._view.seq_search_start.clicked.connect(self.handle_seq_search_start)
        if hasattr(self._view, 'seq_search_next'):
            self._view.seq_search_next.clicked.connect(self.handle_seq_search_next)
        if hasattr(self._view, 'seq_search_reset'):
            self._view.seq_search_reset.clicked.connect(self.handle_seq_search_reset)

        if hasattr(self._view, 'seq_delete_start'):
            self._view.seq_delete_start.clicked.connect(self.handle_seq_delete_start)
        if hasattr(self._view, 'seq_delete_next'):
            self._view.seq_delete_next.clicked.connect(self.handle_seq_delete_next)
        if hasattr(self._view, 'seq_delete_reset'):
            self._view.seq_delete_reset.clicked.connect(self.handle_seq_delete_reset)

        # 顺序表/链表 插入分步按钮（合并为一个：插入/下一步）
        if hasattr(self._view, 'seq_insert_button'):
            self._view.seq_insert_button.clicked.connect(self.handle_seq_insert_toggle)
        if hasattr(self._view, 'seq_insert_reset'):
            self._view.seq_insert_reset.clicked.connect(self.handle_seq_insert_reset)
        # 栈操作按钮
        if hasattr(self._view, 'stack_push_button'):
            self._view.stack_push_button.clicked.connect(self.handle_stack_push)
        if hasattr(self._view, 'stack_pop_button'):
            self._view.stack_pop_button.clicked.connect(self.handle_stack_pop)
        if hasattr(self._view, 'stack_top_button'):
            self._view.stack_top_button.clicked.connect(self.handle_stack_top)
        # Save / Load buttons for structures (implemented for sequential & linked lists)
        if hasattr(self._view, 'save_structure_button'):
            self._view.save_structure_button.clicked.connect(self.handle_save_structure)
        if hasattr(self._view, 'load_structure_button'):
            self._view.load_structure_button.clicked.connect(self.handle_load_structure)

    # 处理BST分步删除演示
    def handle_delete_start(self):
        if self._active_model_name != "bst": return
        self.handle_delete_reset()
        active_model = self._models["bst"]
        value_str = self._view.value_input.text()
        if not value_str: return

        # 根据当前模式决定是否将输入强制转换为整数
        val_int = None
        if self._active_model_name != "huffman_tree":
            try:
                val_int = int(value_str)
            except ValueError:
                return
            # 为了兼容后续代码，保留 name `value` 指向整数
            value = val_int
        self._delete_path_iterator = active_model.delete_path(value)
        self._delete_history = [] # 清空历史
        self._current_delete_step = -1

        # 启用/禁用按钮进入“删除模式”
        if hasattr(self._view, 'next_delete_step_button'):
            self._view.next_delete_step_button.setEnabled(True)
        if hasattr(self._view, 'reset_delete_button'):
            self._view.reset_delete_button.setEnabled(True)
        self._view.insert_button.setEnabled(False)
        self._view.delete_button.setEnabled(False)
        self._view.start_delete_button.setEnabled(False)
        self.handle_delete_next()

    def handle_huffman_draw(self):
        """处理哈夫曼树的立即绘制请求"""
        self.handle_huffman_build_reset() # 先重置状态
        input_str = self._view.huffman_input.text()
        if not input_str: return

        frequencies = {}
        try:
            pairs = input_str.split(',')
            for pair in pairs:
                if ':' not in pair: continue
                char, weight_str = pair.split(':', 1)
                char = char.strip()
                weight = int(weight_str.strip())
                if not char: continue
                frequencies[char] = weight
            
            if not frequencies: raise ValueError("输入数据无效或为空。")

            # 创建模型并直接构建
            huffman_model = HuffmanTree()
            huffman_model.build_from_frequencies(frequencies)
            self._models["huffman_tree"] = huffman_model
            
            # 更新视图
            self.update_view()

            # 允许用户重置已绘制的哈夫曼树
            try:
                self._view.huffman_reset_button.setEnabled(True)
                # 未进入分步演示模式，因此 prev/next 保持禁用，start 保持可用以便用户可选择开始演示
                self._view.huffman_prev_step_button.setEnabled(False)
                self._view.huffman_next_step_button.setEnabled(False)
                self._view.huffman_start_button.setEnabled(True)
            except Exception:
                pass

        except (ValueError, IndexError) as e:
            self._current_huffman_build_state = {"text": f"输入错误: {e}"}
            self.update_view()

    def handle_huffman_random_generate(self):
        """为哈夫曼输入框随机生成 a~g 的若干字母及其权重，并注入到输入框中。格式: "a:5, b:9, ...""" 
        letters = list('abcdefg')
        # 随机决定包含几个字母（至少1个，最多7个）
        k = random.randint(1, len(letters))
        chosen = random.sample(letters, k)
        pairs = []
        for ch in chosen:
            weight = random.randint(1, 99)
            pairs.append(f"{ch}:{weight}")
        result = ", ".join(pairs)
        try:
            self._view.huffman_input.setText(result)
            # 仅填入输入框，不自动开始构建；用户可以选择立刻绘制或开始演示
        except Exception:
            # 容错：若视图或输入框不存在，忽略
            pass

    def handle_bst_random_generate(self):
        """为BST构建面板生成随机序列并填入输入框。序列长度随机(3-12)，元素为1-100的不重复整数。"""
        try:
            k = random.randint(3, 12)
            nums = random.sample(range(1, 101), k)
            seq = ",".join(str(n) for n in nums)
            self._view.bst_build_input.setText(seq)
        except Exception:
            # 容错：如果视图不存在或设置失败，忽略
            pass

    def handle_knapsack_run(self):
        """Parse inputs and start step-by-step backtracking demo with generator."""
        try:
            items_str = self._view.knap_items_input.text()
            cap_str = self._view.knap_capacity_input.text()
        except Exception:
            return

        if not items_str or not cap_str:
            try:
                self._view.display_info_text("请输入 items 和 背包容量。格式: w1 或 w1:v1, w2 或 w2:v2, ...")
            except Exception:
                pass
            return

        try:
            capacity = int(cap_str)
        except Exception:
            try:
                self._view.display_info_text("容量应为整数。")
            except Exception:
                pass
            return

        pairs = [p.strip() for p in items_str.split(',') if p.strip()]
        weights = []
        values = []
        for p in pairs:
            if ':' in p:
                w_str, v_str = p.split(':', 1)
                try:
                    w = int(w_str.strip())
                    v = int(v_str.strip())
                except Exception:
                    try:
                        self._view.display_info_text(f"无法解析项: {p}. 使用 w 或 w:v (整数) 格式。")
                    except Exception:
                        pass
                    return
            else:
                try:
                    w = int(p)
                    v = w
                except Exception:
                    try:
                        self._view.display_info_text(f"无法解析项: {p}. 使用 w 或 w:v (整数) 格式。")
                    except Exception:
                        pass
                    return
            weights.append(w)
            values.append(v)

        if not weights:
            try:
                self._view.display_info_text("没有可用项。")
            except Exception:
                pass
            return

        # 全局预判: 如果所有物品总重量小于目标容量，则直接无解
        try:
            if sum(weights) < capacity:
                try:
                    self._view.display_info_text("物品总重量不足，无解")
                    # 禁用下一步按钮，防止用户点击后看到“演示结束”或异常
                    if hasattr(self._view, 'knap_next_step_button'):
                        self._view.knap_next_step_button.setEnabled(False)
                except Exception:
                    pass
                return
        except Exception:
            # 如果计算总和时报错（例如 weights 不是数值列表），忽略并继续
            pass

        # 初始化背包演示状态
        self._knapsack_items = [(w, v) for w, v in zip(weights, values)]
        self._knapsack_weights = weights
        self._knapsack_capacity = capacity
        self._knapsack_stack = []
        self._knapsack_remaining = capacity
        self._knapsack_discarded = []  # 初始化被丢弃列表
        
        # 创建生成器并进行逐步演示
        self._knapsack_gen = knapsac.solve_subset_sum_backtracking_gen(weights, capacity)
        
        # 启用下一步按钮，但不自动执行第一步
        if hasattr(self._view, 'knap_next_step_button'):
            self._view.knap_next_step_button.setEnabled(True)
        
        # 显示初始状态（空栈、空丢弃区）
        try:
            self._view.draw_knapsack_backtracking_demo(
                items=self._knapsack_items,
                weights=self._knapsack_weights,
                current_stack_indices=self._knapsack_stack,
                discarded_indices=self._knapsack_discarded,
                remaining_capacity=self._knapsack_remaining,
                capacity=self._knapsack_capacity,
                highlighted_action=None
            )
        except Exception as e:
            try:
                self._view.display_info_text(f"绘制初始状态失败: {e}")
            except Exception:
                pass

    def handle_knapsack_step_next(self):
        """从生成器获取下一步事件并更新视图。"""
        if self._knapsack_gen is None:
            return
        
        try:
            event = next(self._knapsack_gen)
        except StopIteration:
            if hasattr(self._view, 'knap_next_step_button'):
                self._view.knap_next_step_button.setEnabled(False)
            return

        # 引入颜色 (或者在文件头 import)
        from PySide6.QtGui import QColor

        action = event.get("action")
        
        # 预定义变量，用于后续显示
        msg = None
        msg_color = QColor("black")
        highlighted = None
        should_disable_button = False

        # 1. 处理逻辑与状态更新
        if action == "push":
            idx = event.get("index")
            w = event.get("weight")
            rem = event.get("remaining")
            self._knapsack_stack.append(idx)
            self._knapsack_remaining = rem
            
            msg = (
                f"【尝试放入】\n"
                f"物品索引: {idx}\n"
                f"重量: {w}\n"
                f"----------------\n"
                f"放入后剩余容量: {rem}"
            )
            msg_color = QColor("#2e8b57") # 海洋绿
            highlighted = {"type": "push", "index": idx}

        elif action == "pop":
            idx = event.get("index")
            rem = event.get("remaining")
            if idx in self._knapsack_stack:
                self._knapsack_stack.remove(idx)
                if idx not in self._knapsack_discarded:
                    self._knapsack_discarded.append(idx)
            self._knapsack_remaining = rem

            msg = (
                f"【回溯/移出】\n"
                f"物品索引: {idx}\n"
                f"----------------\n"
                f"原因: 后续路径无解\n"
                f"尝试其他分支..."
            )
            msg_color = QColor("#cd5c5c") # 印度红
            highlighted = {"type": "pop", "index": idx}

        elif action == "found":
            self._knapsack_stack = event.get("indices", [])
            total = event.get('total')
            
            msg = (
                f" 【找到完美解】 \n"
                f"------------------\n"
                f"所选物品: {self._knapsack_stack}\n"
                f"总重量: {total}\n"
                f"正好填满背包！"
            )
            msg_color = QColor("#006400") # 深绿
            highlighted = None
            should_disable_button = True

        else:
            # action == "no_solution"
            msg = (
                "【搜索结束：无解】\n"
                "----------------------\n"
                "已遍历所有可能的组合分支。\n"
                "原因判定：\n"
                "1. 可用物品组合无法填满剩余容量。\n"
                "2. 或所有组合总和不等于目标值。\n"
                "结论：不存在满足条件的子集。"
            )
            msg_color = QColor("red")
            highlighted = None
            should_disable_button = True

        # 核心修改：先画图（这会清空场景）
        try:
            self._view.draw_knapsack_backtracking_demo(
                items=self._knapsack_items,
                weights=self._knapsack_weights,
                current_stack_indices=self._knapsack_stack,
                discarded_indices=self._knapsack_discarded,
                remaining_capacity=self._knapsack_remaining,
                capacity=self._knapsack_capacity,
                highlighted_action=highlighted
            )
        except Exception as e:
            print(f"Drawing error: {e}")

        # 核心修改：后写字（画在图层之上）
        if msg:
            try:
                self._view.display_info_text(msg, color=msg_color)
            except Exception:
                pass

        # 处理按钮状态
        if should_disable_button:
            if hasattr(self._view, 'knap_next_step_button'):
                self._view.knap_next_step_button.setEnabled(False)



    def handle_knapsack_reset(self):
        """重置背包演示为初始状态。"""
        # 重置所有状态变量
        self._knapsack_gen = None
        self._knapsack_items = None
        self._knapsack_weights = None
        self._knapsack_capacity = None
        self._knapsack_stack = []
        self._knapsack_remaining = None
        self._knapsack_discarded = []
        
        # 禁用下一步按钮
        if hasattr(self._view, 'knap_next_step_button'):
            self._view.knap_next_step_button.setEnabled(False)
        
        # 清空输入框
        try:
            self._view.knap_items_input.clear()
            self._view.knap_capacity_input.clear()
        except Exception:
            pass
        
        # 重新绘制初始状态（空栈、空丢弃区）
        try:
            self._view.draw_knapsack_backtracking_demo(
                items=[],
                weights=[],
                current_stack_indices=[],
                discarded_indices=[],
                remaining_capacity=0,
                capacity=0
            )
        except Exception:
            pass

    # Infix -> Postfix 演示处理
    def handle_infix_run(self):
        """准备并启动中缀->后缀的生成器演示（不自动执行第一步）。"""
        try:
            expr = self._view.infix_input.text()
        except Exception:
            expr = None

        if not expr:
            try:
                self._view.display_info_text("请输入中缀表达式后再运行", QColor("red"))
            except Exception:
                pass
            return

        # 初始化状态
        self._infix_expr = expr
        self._infix_gen = infix_to_postfix.infix_to_postfix_gen(expr)

        # 准备视图（清空栈/后缀显示），启用下一步按钮
        try:
            # 使用新的专用绘制方法初始化视图
            self._view.draw_infix_postfix_demo([], "", "", "已准备好：点击 下一步 查看每一步")
            if hasattr(self._view, 'infix_next_step_button'):
                self._view.infix_next_step_button.setEnabled(True)
        except Exception:
            pass

    def handle_infix_step_next(self):
        """从生成器取得下一步事件并在视图中更新显示。"""
        if self._infix_gen is None:
            try:
                self._view.display_info_text("请先运行演示（Run）", QColor("red"))
            except Exception:
                pass
            return

        try:
            event = next(self._infix_gen)
        except StopIteration:
            # 迭代器结束
            self._infix_gen = None
            if hasattr(self._view, 'infix_next_step_button'):
                self._view.infix_next_step_button.setEnabled(False)
            try:
                self._view.display_info_text("演示已结束。", QColor("black"))
            except Exception:
                pass
            return

        # 解析事件并更新视图
        stack_list = event.get('stack', [])
        postfix = event.get('postfix', '')
        action_text = event.get('action_text', '')
        step_type = event.get('step_type')
        token = event.get('token', '')

        try:
            # 使用专用的中缀->后缀演示绘制方法
            self._view.draw_infix_postfix_demo(stack_list, postfix, token, action_text)
        except Exception:
            pass

        # 如果转换成功完成，自动将结果填入下方的“后缀求值”输入框
        if step_type == "done":
            # 将列表拼接成空格分隔的字符串 (e.g., "3 4 +")
            result_str = " ".join(str(x) for x in postfix)
            
            # 填入 UI
            if hasattr(self._view, 'postfix_eval_input'):
                try:
                    self._view.postfix_eval_input.setText(result_str)
                except Exception:
                    pass
            
            # 更新提示文本，告知用户已自动填充
            try:
                self._view.display_info_text(f"转换完成！结果 “{result_str}” 已自动填入下方求值框。", QColor("#006400"))
            except Exception:
                pass

        # 如果遇到完成或错误事件，禁用下一步
        if step_type in ("done", "error"):
            self._infix_gen = None
            if hasattr(self._view, 'infix_next_step_button'):
                self._view.infix_next_step_button.setEnabled(False)

    def handle_infix_reset(self):
        """重置中缀->后缀演示为初始状态（清空输入与视图）。"""
        self._infix_gen = None
        self._infix_expr = None
        if hasattr(self._view, 'infix_next_step_button'):
            self._view.infix_next_step_button.setEnabled(False)
        try:
            self._view.infix_input.clear()
        except Exception:
            pass

        # 确保清除画面
        try:
            self._view.clear_all_visuals()
        except Exception:
            pass

    def handle_postfix_eval_run(self):
        """启动后缀求值演示"""
        try:
            expr = self._view.postfix_eval_input.text()
        except Exception:
            expr = None

        if not expr:
            try:
                self._view.display_info_text("请输入后缀表达式 (如: 3 4 +)", QColor("red"))
            except Exception:
                pass
            return

        # 互斥逻辑：如果正在运行中缀转后缀，先停掉它，避免画面冲突
        try:
            self.handle_infix_reset()
        except Exception:
            pass

        # 初始化
        self._postfix_eval_gen = postfix_evaluation.postfix_evaluation_gen(expr)
        
        # 准备视图
        try:
            self._view.draw_postfix_evaluation_demo([], "START", "准备就绪：点击 下一步 开始计算")
            if hasattr(self._view, 'postfix_eval_next_button'):
                self._view.postfix_eval_next_button.setEnabled(True)
        except Exception:
            pass

    def handle_postfix_eval_next(self):
        """下一步"""
        if self._postfix_eval_gen is None:
            return

        try:
            event = next(self._postfix_eval_gen)
        except StopIteration:
            self._postfix_eval_gen = None
            if hasattr(self._view, 'postfix_eval_next_button'):
                self._view.postfix_eval_next_button.setEnabled(False)
            try:
                self._view.display_info_text("计算演示结束。", QColor("black"))
            except Exception:
                pass
            return

        stack_list = event.get('stack', [])
        token = event.get('token', '')
        action_text = event.get('action_text', '')
        step_type = event.get('step_type')
        calc_info = event.get('calc_info') # 获取计算详情

        try:
            self._view.draw_postfix_evaluation_demo(stack_list, token, action_text, calc_info)
        except Exception:
            pass

        if step_type in ("done", "error"):
            self._postfix_eval_gen = None
            if hasattr(self._view, 'postfix_eval_next_button'):
                self._view.postfix_eval_next_button.setEnabled(False)

    def handle_postfix_eval_reset(self):
        """重置"""
        self._postfix_eval_gen = None
        if hasattr(self._view, 'postfix_eval_next_button'):
            self._view.postfix_eval_next_button.setEnabled(False)
        
        try:
            # 清空后缀表达式输入框
            if hasattr(self._view, 'postfix_eval_input'):
                self._view.postfix_eval_input.clear()
            self._view.clear_all_visuals()
        except Exception:
            pass

    def handle_algorithm_change(self, algo_name):
        """切换算法演示面板：显示对应的控件并重置该算法的状态。"""
        try:
            # 获取所有算法面板的引用（如果存在）
            knap_widget = getattr(self._view, 'knap_widget', None)
            infix_widget = getattr(self._view, 'infix_widget', None)
            paren_widget = getattr(self._view, 'paren_match_widget', None)

            # 切换到【背包问题】
            if algo_name == 'knapsack':
                if knap_widget: knap_widget.setVisible(True)
                if infix_widget: infix_widget.setVisible(False)
                if paren_widget: paren_widget.setVisible(False)
                # 切换时重置画布
                self.handle_knapsack_reset()

            # 切换到【表达式求值 (中缀转后缀 + 求值)】
            elif algo_name == 'infix':
                if knap_widget: knap_widget.setVisible(False)
                if infix_widget: infix_widget.setVisible(True)
                if paren_widget: paren_widget.setVisible(False)
                # 切换时重置画布
                self.handle_infix_reset()
                self.handle_postfix_eval_reset()

            # 切换到【括号匹配】
            elif algo_name == 'paren_match':
                if knap_widget: knap_widget.setVisible(False)
                if infix_widget: infix_widget.setVisible(False)
                if paren_widget: paren_widget.setVisible(True)
                # 可选：切换时重置画布
                self.handle_paren_match_reset()
                
        except Exception as e:
            print(f"Error changing algorithm mode: {e}")

    def handle_delete_next(self):
        # 如果当前不是最后一步，直接从历史记录中读取下一步
        if self._current_delete_step < len(self._delete_history) - 1:
            self._current_delete_step += 1
            state = self._delete_history[self._current_delete_step]
            self._models["bst"].root = state["tree"]
            self._current_delete_info = state
            self._highlighted_node_key = getattr(state.get("highlight_node"), "key", None)
            self.update_view()
            self._update_delete_buttons_state()

        

        # 否则，从生成器获取新步骤
        if self._delete_path_iterator:
            try:
                state = next(self._delete_path_iterator)
                # 深拷贝树的状态
                state_copy = {
                    "tree": copy.deepcopy(state["tree"]),
                    "text": state.get("text", ""),
                    "highlight_node": state.get("highlight_node")
                }
                self._delete_history.append(state_copy)
                self._current_delete_step += 1
                
                self._models["bst"].root = state["tree"]
                self._current_delete_info = state
                self._highlighted_node_key = getattr(state.get("highlight_node"), "key", None)
                self.update_view()
            except StopIteration:
                self._delete_path_iterator = None # 标记迭代器已耗尽
                if hasattr(self._view, 'next_delete_step_button'):
                    self._view.next_delete_step_button.setEnabled(False)
            self._update_delete_buttons_state()

    def handle_delete_prev(self):
        if self._current_delete_step > 0:
            self._current_delete_step -= 1
            state = self._delete_history[self._current_delete_step]
            
            # 直接使用历史记录中的树
            self._models["bst"].root = state['tree']
            self._current_delete_info = state
            self._highlighted_node_key = getattr(state.get("highlight_node"), "key", None)

            self.update_view()
            self._update_delete_buttons_state()

    # 括号匹配 演示处理
    def handle_paren_match_run(self):
        try:
            expr = self._view.paren_input.text()
        except Exception:
            expr = ""

        if not expr:
            try:
                self._view.display_info_text("请输入字符串", QColor("red"))
            except Exception:
                pass
            return

        self._paren_match_gen = parentheses_matching.parentheses_matching_gen(expr)
        try:
            self._view.draw_parentheses_matching_demo(expr, -1, [], "准备就绪：点击 下一步 开始", "start")
            if hasattr(self._view, 'paren_next_button'):
                self._view.paren_next_button.setEnabled(True)
        except Exception:
            pass

    def handle_paren_match_next(self):
        if self._paren_match_gen is None:
            return
        try:
            event = next(self._paren_match_gen)
        except StopIteration:
            self._paren_match_gen = None
            if hasattr(self._view, 'paren_next_button'):
                self._view.paren_next_button.setEnabled(False)
            try:
                self._view.display_info_text("检测结束。", QColor("black"))
            except Exception:
                pass
            return

        expr = self._view.paren_input.text() if hasattr(self._view, 'paren_input') else ""
        idx = event.get('index')
        stack = event.get('stack', [])
        action = event.get('action_text', '')
        step_type = event.get('step_type')
        try:
            self._view.draw_parentheses_matching_demo(expr, idx, stack, action, step_type)
        except Exception:
            pass

        if step_type in ("done_success", "error", "error_mismatch", "error_unbalanced"):
            self._paren_match_gen = None
            if hasattr(self._view, 'paren_next_button'):
                self._view.paren_next_button.setEnabled(False)

    def handle_paren_match_reset(self):
        self._paren_match_gen = None
        if hasattr(self._view, 'paren_next_button'):
            self._view.paren_next_button.setEnabled(False)
        try:
            self._view.clear_all_visuals()
        except Exception:
            pass

    def _update_delete_buttons_state(self):
        if hasattr(self._view, 'prev_delete_step_button'):
            self._view.prev_delete_step_button.setEnabled(self._current_delete_step > 0)
        
        is_last_step = False
        if self._delete_path_iterator:
            # 我们不知道生成器是否结束，除非我们尝试next()
            # 但我们不能真的消耗它。所以我们只在历史记录和当前步数不匹配时认为还有下一步
            is_last_step = self._current_delete_step >= len(self._delete_history) -1
        
        if hasattr(self._view, 'next_delete_step_button'):
             # 如果迭代器已经耗尽（没有更多历史步骤可生成），则禁用“下一步”
            is_iterator_exhausted = self._current_delete_step == len(self._delete_history) - 1 and self._delete_path_iterator is None
            self._view.next_delete_step_button.setEnabled(not is_iterator_exhausted)

    def handle_delete_reset(self):
        self._delete_path_iterator = None
        self._current_delete_info = None
        self._highlighted_node_key = None
        self._delete_history = []
        self._current_delete_step = -1

        if hasattr(self._view, 'prev_delete_step_button'):
            self._view.prev_delete_step_button.setEnabled(False)
        if hasattr(self._view, 'next_delete_step_button'):
            self._view.next_delete_step_button.setEnabled(False)
        if hasattr(self._view, 'reset_delete_button'):
            self._view.reset_delete_button.setEnabled(False)
        
        self._view.insert_button.setEnabled(True)
        self._view.delete_button.setEnabled(True)
        self._view.start_delete_button.setEnabled(True)
        self.update_view()


    # 顺序表 分步查找/删除
    def handle_seq_search_start(self):
        # 支持顺序表与链表的分步查找
        if self._active_model_name not in ("sequential_list", "linked_list"): return
        # 重置已有状态
        self.handle_seq_search_reset()
        # 弹出输入对话框获取要查找的整数
        try:
            value, ok = QInputDialog.getInt(self._view, "查询", "输入要查询的元素:")
            if not ok:
                return
        except Exception:
            return

        self._seq_search_target = value

        # 创建生成器：逐个索引遍历（对顺序表与链表相同：逐节点遍历）
        def gen():
            elems = self._models[self._active_model_name].get_all_elements()
            for i, v in enumerate(elems):
                yield {"index": i, "found": (v == value)}
                if v == value:
                    return

        self._seq_search_iterator = gen()
        # 更新按钮状态
        self._view.seq_search_next.setEnabled(True)
        self._view.seq_search_reset.setEnabled(True)
        self._view.seq_search_start.setEnabled(False)
        # 禁用主操作避免冲突
        self._view.insert_button.setEnabled(False)
        self._view.delete_button.setEnabled(False)
        # 初始提示：根据当前模式给出教学性说明
        try:
            if self._active_model_name == 'sequential_list':
                self._view.display_info_text("顺序表（数组驱动）：支持随机访问索引。本演示将从 index=0 开始检查每个位置，匹配目标即停止。")
            else:
                self._view.display_info_text("链表（节点驱动）：需要从头节点开始逐一遍历到目标位置。本演示将从头节点开始逐个检查每个节点。")
        except Exception:
            pass
        # 自动进行第一步以高亮第一个元素
        self.handle_seq_search_next()

    def handle_seq_search_next(self):
        if not self._seq_search_iterator:
            return
        try:
            state = next(self._seq_search_iterator)
            idx = state.get('index')
            found = state.get('found', False)
            self._seq_search_current_index = idx
            # 构造信息文本
            if found:
                self._view.display_info_text(f"找到目标 {self._seq_search_target}，位置 index={idx}")
                # 查找完成
                self._view.seq_search_next.setEnabled(False)
                # 自动重置查找状态（延迟），结束演示并恢复主操作按钮
                try:
                    QTimer.singleShot(self._auto_reset_delay_ms, self.handle_seq_search_reset)
                except Exception:
                    pass
            self.update_view()
        except StopIteration:
            self._view.seq_search_next.setEnabled(False)
            self._view.display_info_text(f"查找结束: 未找到 {self._seq_search_target} 或已完成遍历。")
            self._seq_search_iterator = None
            # 自动重置查找演示（延迟）
            try:
                QTimer.singleShot(self._auto_reset_delay_ms, self.handle_seq_search_reset)
            except Exception:
                pass

    def handle_seq_search_reset(self):
        self._seq_search_iterator = None
        self._seq_search_target = None
        self._seq_search_current_index = None
        self._linked_reconnect_info = None
        # 清除视图缓存的 info 文本，确保自动重置时提示也消失
        try:
            if hasattr(self._view, '_cached_info_text'):
                self._view._cached_info_text = None
            if hasattr(self._view, '_cached_info_item') and getattr(self._view, '_cached_info_item') is not None:
                try:
                    self._view.scene.removeItem(self._view._cached_info_item)
                except Exception:
                    pass
                self._view._cached_info_item = None
        except Exception:
            pass
        try:
            self._view.seq_search_start.setEnabled(True)
            self._view.seq_search_next.setEnabled(False)
            self._view.seq_search_reset.setEnabled(False)
        except Exception:
            pass
        # 恢复主操作按钮
        try:
            self._view.insert_button.setEnabled(True)
            self._view.delete_button.setEnabled(True)
        except Exception:
            pass
        self.update_view()

    def handle_get_by_index(self, index):
        """
        AI 专用：直接高亮显示指定索引的元素（适用于顺序表和链表）
        """
        if self._active_model_name not in ["sequential_list", "linked_list"]:
            try:
                self._view.display_info_text("当前结构不支持按索引查看")
            except Exception:
                pass
            return

        # 先重置之前的状态
        try:
            self.handle_seq_search_reset()
        except Exception:
            pass

        active_model = self._models.get(self._active_model_name)
        try:
            elements = active_model.get_all_elements()
        except Exception:
            # 退化为空列表
            elements = []
        
        if 0 <= index < len(elements):
            value = elements[index]
            # 设置高亮索引，这会让 update_view 绘制时把该方块标红/变色
            self._seq_search_current_index = index
            # 显示信息
            try:
                self._view.display_info_text(f"索引 [{index}] 的值为: {value}")
            except Exception:
                pass
            self.update_view()
            # 1.5秒后自动取消高亮
            try:
                QTimer.singleShot(1500, self.handle_seq_search_reset)
            except Exception:
                pass
        else:
            try:
                self._view.display_info_text(f"索引 {index} 越界 (当前长度: {len(elements)})", QColor("red"))
            except Exception:
                pass

    def handle_seq_delete_start(self):
        # 支持顺序表与链表的分步删除；链表会展示重连步骤
        if self._active_model_name not in ("sequential_list", "linked_list"): return
        self.handle_seq_delete_reset()
        try:
            value, ok = QInputDialog.getInt(self._view, "删除", "输入要删除的元素:")
            if not ok:
                return
        except Exception:
            return

        self._seq_delete_target = value
        # 初始提示：说明删除的不同实现（顺序表需要移动/覆盖，链表需要重连指针）
        try:
            if self._active_model_name == 'sequential_list':
                self._view.display_info_text("顺序表删除：数组元素将向左移动以填补空位，最后 length--。演示会逐步显示每次移动和尾部清空。")
            else:
                self._view.display_info_text("链表删除：找到目标节点后会将前驱节点的 next 指向目标的 next，从而断开并移除目标节点。演示将在重连步骤显示弧线指示。")
        except Exception:
            pass
        if self._active_model_name == 'sequential_list':
            def gen_del():
                elems = self._models['sequential_list'].get_all_elements()
                n = len(elems)
                # 找到第一个匹配的索引
                target_idx = None
                for i, v in enumerate(elems):
                    if v == value:
                        target_idx = i
                        break
                    yield {"index": i, "deleted": False}

                if target_idx is None:
                    # 未找到，结束
                    return

                # 模拟移动：对于 j 从 target_idx+1 到 n-1，依次将 elems[j] 移到位置 j-1
                working = elems.copy()
                for j in range(target_idx + 1, n):
                    working[j-1] = working[j]
                    display = working.copy()
                    # 将当前中间状态传给视图
                    yield {"display_array": display, "index": j-1, "deleted": False, "step": "shift", "from": j, "to": j-1}

                # 现在最后一位应显示为空
                display = working.copy()
                display[-1] = None
                yield {"display_array": display, "index": n-1, "deleted": False, "step": "clear_tail"}

                # 执行模型删除（真正缩减长度）
                try:
                    self._models['sequential_list'].delete(target_idx)
                except Exception:
                    pass

                # 最终返回已删除的信号，视图将以模型为准渲染最终数组（长度已减一）
                yield {"index": target_idx, "deleted": True}

            self._seq_delete_iterator = gen_del()

        else: # linked_list
            def gen_del_linked():
                elems = self._models['linked_list'].get_all_elements()
                prev = None
                for i, v in enumerate(elems):
                    # 遍历到当前节点
                    if v == value:
                        # 首先 yield 一个用于显示重连的步骤（不修改模型）
                        next_idx = i+1 if i+1 < len(elems) else None
                        yield {"index": i, "deleted": False, "reconnect": {"prev": prev, "next": next_idx, "at": i}}
                        # 当下一次继续时，真正执行删除操作
                        try:
                            self._models['linked_list'].delete(i)
                        except Exception:
                            pass
                        yield {"index": i, "deleted": True}
                        return
                    else:
                        yield {"index": i, "deleted": False}
                    prev = i

            self._seq_delete_iterator = gen_del_linked()

        self._view.seq_delete_next.setEnabled(True)
        self._view.seq_delete_reset.setEnabled(True)
        self._view.seq_delete_start.setEnabled(False)
        self._view.insert_button.setEnabled(False)
        self._view.delete_button.setEnabled(False)
        # 先执行第一步
        self.handle_seq_delete_next()

    def handle_seq_delete_next(self):
        if not self._seq_delete_iterator:
            return
        try:
            state = next(self._seq_delete_iterator)
            # 支持生成器返回的中间 display_array（用于显示移动/清空尾部的中间状态）
            display = state.get('display_array')
            self._seq_delete_display_array = display
            idx = state.get('index')
            deleted = state.get('deleted', False)
            reconnect = state.get('reconnect')
            # 如果是链表重连步骤，先展示重连信息并返回等待用户按“下一步”执行删除
            if reconnect:
                self._seq_delete_current_index = idx
                self._linked_reconnect_info = reconnect
                self._view.display_info_text(f"找到目标 {self._seq_delete_target}，将在 prev={reconnect.get('prev')} 和 next={reconnect.get('next')} 之间重连。按 下一步 执行删除。")
                self.update_view()
                return
            self._seq_delete_current_index = idx
            if deleted:
                self._view.display_info_text(f"已删除目标 {self._seq_delete_target}，原位置 index={idx}")
                # 删除后不允许继续下一步
                self._view.seq_delete_next.setEnabled(False)
                # 清除 iterator 表示完成
                self._seq_delete_iterator = None
                self._linked_reconnect_info = None
                # 删除完成后清除任何中间显示数组，视图将以模型为准渲染最终数组
                self._seq_delete_display_array = None
                # 自动重置删除演示（延迟），恢复主按钮状态
                try:
                    QTimer.singleShot(self._auto_reset_delay_ms, self.handle_seq_delete_reset)
                except Exception:
                    pass
            self.update_view()
        except StopIteration:
            self._view.seq_delete_next.setEnabled(False)
            self._seq_delete_iterator = None
            self._view.display_info_text(f"删除结束: 未找到 {self._seq_delete_target} 或已完成遍历。")
            # 自动重置删除演示（延迟）
            try:
                QTimer.singleShot(self._auto_reset_delay_ms, self.handle_seq_delete_reset)
            except Exception:
                pass

    def handle_seq_delete_reset(self):
        self._seq_delete_iterator = None
        self._seq_delete_target = None
        self._seq_delete_current_index = None
        self._seq_delete_display_array = None
        # 清除视图缓存的 info 文本，确保自动重置时提示也消失
        try:
            if hasattr(self._view, '_cached_info_text'):
                self._view._cached_info_text = None
            if hasattr(self._view, '_cached_info_item') and getattr(self._view, '_cached_info_item') is not None:
                try:
                    self._view.scene.removeItem(self._view._cached_info_item)
                except Exception:
                    pass
                self._view._cached_info_item = None
        except Exception:
            pass
        try:
            self._view.seq_delete_start.setEnabled(True)
            self._view.seq_delete_next.setEnabled(False)
            self._view.seq_delete_reset.setEnabled(False)
        except Exception:
            pass
        try:
            self._view.insert_button.setEnabled(True)
            self._view.delete_button.setEnabled(True)
        except Exception:
            pass
        self.update_view()


    def handle_seq_insert_start(self):
        # 支持链表的分步插入（也可用于顺序表），演示：遍历到索引 -> 放置新节点 -> 显示重连 -> 实际插入
        if self._active_model_name not in ("sequential_list", "linked_list"): return
        # 重置已有状态
        self.handle_seq_insert_reset()
        # 从视图读取索引和值
        try:
            idx_str = self._view.seq_insert_index_input.text()
            val_str = self._view.seq_insert_value_input.text()
            if idx_str is None or val_str is None or idx_str.strip()=="" or val_str.strip()=="":
                return
            # 支持使用 'h' 或 'H' 表示头插（即在头部之前插入）
            if idx_str.strip().lower() == 'h':
                index = -1
            else:
                index = int(idx_str)
            value = int(val_str)
        except Exception:
            return

        self._seq_insert_index = index
        self._seq_insert_value = value
        # 初始提示：说明插入将在两种数据结构上的不同实现
        try:
            if self._active_model_name == 'sequential_list':
                self._view.display_info_text("顺序表插入：数组支持随机访问，本演示会先定位索引（红框），在末尾添加空位，然后逐步将元素右移后放置新元素。")
            else:
                self._view.display_info_text("链表插入：需要从头遍历到插入位置，放置新节点并在重连阶段更新前驱/后继指针，演示将分步显示 place 与 relink。")
        except Exception:
            pass
        if self._active_model_name == 'sequential_list':
            def gen_seq_ins():
                elems = self._models['sequential_list'].get_all_elements()
                # 用户输入的 index 被解释为“在该 index 之后插入”，实际插入位置为 index+1
                n = len(elems)
                insert_pos = max(0, min(index + 1, n))

                # 遍历到 prev（用户输入的 index），在到达时暂停以示意遍历过程
                prev_idx = index
                if prev_idx < 0:
                    prev_idx = -1
                if prev_idx >= n:
                    prev_idx = n - 1

                # 直接将高亮定位到 prev（用户输入的 index），无需逐步遍历演示
                # 如果 prev_idx 为 -1（表示在头部之前插入），高亮第0个位置以便可见
                highlight_idx = prev_idx if prev_idx >= 0 else 0
                yield {"index": highlight_idx}

                # 模拟从尾到插入位置的整体右移：先在 working 上追加一个占位以模拟容量增长，
                # 并先展示这个新增的空位（index = n），然后再从 j=n-1 到 insert_pos 逐步右移元素
                working = elems.copy()
                working.append(None)  # 使长度变为 n+1，索引范围 [0..n]

                # 先展示末尾新增的空位，方便教学观察（用户按下一步后开始移动）
                display = working.copy()
                yield {"display_array": display, "index": n, "inserted": False, "step": "append"}

                for j in range(n - 1, insert_pos - 1, -1):
                    # 将 working[j] 移到 j+1
                    working[j+1] = working[j]
                    # 将当前中间状态传给视图以显示移动
                    display = working.copy()
                    yield {"display_array": display, "index": j+1, "inserted": False, "step": "shift", "from": j, "to": j+1}

                # 在插入位置放置新值（视觉上显示为 place）
                working[insert_pos] = value
                yield {"display_array": working.copy(), "index": insert_pos, "inserted": False, "step": "place"}

                # 执行模型实际插入（缩增底层数组）
                try:
                    self._models['sequential_list'].insert(insert_pos, value)
                except Exception:
                    pass

                # 最终返回已插入信号，视图将以模型为准渲染最终数组
                yield {"index": insert_pos, "inserted": True}

            self._seq_insert_iterator = gen_seq_ins()

        else: # linked_list
            def gen_linked_ins():
                elems = self._models['linked_list'].get_all_elements()
                n = len(elems)

                # 我们将用户输入的 index 解释为“在该 index 之后插入”
                # 因此实际插入位置 at = prev_idx + 1
                raw_idx = self._seq_insert_index
                # 限制 prev_idx 在 [-1, n-1]，prev_idx == -1 表示在头部之前插入（即成为新头）
                prev_idx = raw_idx
                if prev_idx < -1:
                    prev_idx = -1
                if prev_idx >= n:
                    prev_idx = n - 1
                at = prev_idx + 1

                # 计算 next 索引（如果超出则为 None）
                next_idx = at if at < n else None

                # 遍历并在到达 prev_idx 时停下以展示遍历过程
                # 如果 prev_idx == -1（头插），则不遍历直接进入 relink 阶段
                if prev_idx >= 0:
                    for i, v in enumerate(elems):
                        yield {"index": i}
                        if i == prev_idx:
                            break

                # 显示 relink 可视化：prev -> new -> next
                yield {"index": at, "insert": {"at": at, "value": value, "prev": (prev_idx if prev_idx >= 0 else None), "next": next_idx, "phase": 'relink'}}

                # 执行实际插入到 at
                try:
                    self._models['linked_list'].insert(at, value)
                except Exception:
                    pass

                # 最终步骤，标记完成并把已插入位置暴露给视图
                yield {"index": at, "inserted": True}

            self._seq_insert_iterator = gen_linked_ins()

        # 更新按钮状态
        try:
            # 切换合并按钮为“下一步”状态并确保可用
            self._view.seq_insert_button.setText("下一步")
            self._view.seq_insert_button.setEnabled(True)
            self._view.seq_insert_reset.setEnabled(True)
        except Exception:
            pass
        # 禁用主操作避免冲突
        try:
            self._view.insert_button.setEnabled(False)
            self._view.delete_button.setEnabled(False)
        except Exception:
            pass

        # 自动执行第一步以高亮第一个元素
        self.handle_seq_insert_next()


    def handle_seq_insert_toggle(self):
        """合并按钮的处理：
        - 如果当前没有进行中的插入生成器，启动插入（等同于以前的 start），
        - 否则前进一步（等同于以前的 next）。
        """
        try:
            if self._seq_insert_iterator:
                self.handle_seq_insert_next()
            else:
                self.handle_seq_insert_start()
        except Exception:
            pass

    def handle_seq_insert_next(self):
        if not self._seq_insert_iterator:
            return
        try:
            state = next(self._seq_insert_iterator)
            # 支持生成器返回的中间 display_array（用于显示右移/放置的新节点）
            display = state.get('display_array')
            self._seq_insert_display_array = display
            idx = state.get('index')
            insert = state.get('insert')
            inserted = state.get('inserted', False)
            # 如果生成器返回了展示数组（中间移动或放置阶段），优先展示并等待下一步
            if display is not None:
                # 给出简短提示并更新视图
                step = state.get('step')
                if step == 'shift':
                    self._view.display_info_text(f"正在将 index={state.get('from')} 的元素移动到 index={state.get('to')}。")
                    # 高亮当前正在被移动的源索引
                    try:
                        self._seq_insert_current_index = int(state.get('from'))
                    except Exception:
                        self._seq_insert_current_index = None
                elif step == 'place':
                    self._view.display_info_text(f"在 index={idx} 放置新元素 {self._seq_insert_value}（准备插入）。")
                    # 高亮放置位置
                    try:
                        self._seq_insert_current_index = int(idx)
                    except Exception:
                        self._seq_insert_current_index = None
                elif step == 'append':
                    self._view.display_info_text(f"在末尾添加一个空位，index={idx}。")
                    try:
                        self._seq_insert_current_index = int(idx)
                    except Exception:
                        self._seq_insert_current_index = None
                self.update_view()
                return
            self._seq_insert_current_index = idx
            if insert:
                # 传递给视图显示 place/relink 阶段
                self._linked_insert_info = insert
                phase = insert.get('phase')
                if phase == 'place':
                    self._view.display_info_text(f"已定位到 index={idx}，在下方放置新节点 {insert.get('value')}。按 下一步 显示连接过程。",)
                else:
                    self._view.display_info_text(f"显示连接过程：prev={insert.get('prev')} -> 新节点 -> next={insert.get('next')}。按 下一步 完成插入。")
                self.update_view()
                return

            if inserted:
                self._view.display_info_text(f"已在 index={idx} 插入元素 {self._seq_insert_value}。")
                # 完成后禁用下一步
                try:
                    # 恢复合并按钮初始文本并禁用，等待 reset
                    self._view.seq_insert_button.setText("插入/下一步")
                    self._view.seq_insert_button.setEnabled(False)
                except Exception:
                    pass
                # 清理插入状态
                self._seq_insert_iterator = None
                self._linked_insert_info = None
                # 删除任何中间可视化数组，视图将以模型为准渲染最终数组
                self._seq_insert_display_array = None
                self._seq_insert_current_index = None
                # 自动重置插入演示（延迟），恢复主操作按钮
                try:
                    QTimer.singleShot(self._auto_reset_delay_ms, self.handle_seq_insert_reset)
                except Exception:
                    pass
            self.update_view()

        except StopIteration:
            try:
                self._view.seq_insert_button.setText("插入/下一步")
                self._view.seq_insert_button.setEnabled(False)
            except Exception:
                pass
            self._seq_insert_iterator = None
            self._view.display_info_text("插入演示结束。")
            # 自动重置插入演示（延迟）
            try:
                QTimer.singleShot(self._auto_reset_delay_ms, self.handle_seq_insert_reset)
            except Exception:
                pass


    def handle_seq_insert_reset(self):
        self._seq_insert_iterator = None
        self._seq_insert_index = None
        self._seq_insert_value = None
        self._seq_insert_current_index = None
        self._linked_insert_info = None
        self._seq_insert_display_array = None
        # 清除视图缓存的 info 文本，确保自动重置时提示也消失
        try:
            if hasattr(self._view, '_cached_info_text'):
                self._view._cached_info_text = None
            if hasattr(self._view, '_cached_info_item') and getattr(self._view, '_cached_info_item') is not None:
                try:
                    self._view.scene.removeItem(self._view._cached_info_item)
                except Exception:
                    pass
                self._view._cached_info_item = None
        except Exception:
            pass
        try:
            # 恢复合并按钮初始状态
            self._view.seq_insert_button.setEnabled(True)
            self._view.seq_insert_button.setText("插入/下一步")
            self._view.seq_insert_reset.setEnabled(False)
        except Exception:
            pass
        try:
            self._view.insert_button.setEnabled(True)
            self._view.delete_button.setEnabled(True)
        except Exception:
            pass
        self.update_view()


    def handle_avl_prev(self):
        """处理AVL树的上一步操作"""
        if self._current_avl_step > 0:
            self._current_avl_step -= 1
            # 从历史记录中恢复AVL树状态（兼容旧的直接存root或新的{root,info}格式）
            state = self._avl_history[self._current_avl_step]
            avl_tree = AVLTree()
            if isinstance(state, dict) and "root" in state:
                # 使用深拷贝恢复一份干净的树，防止与后续操作共享引用
                avl_tree.root = copy.deepcopy(state["root"])
                # 也深拷贝 info，以防视图修改它
                self._current_avl_info = copy.deepcopy(state.get("info"))
                snapshot = state.get("snapshot")
            else:
                avl_tree.root = copy.deepcopy(state)
                self._current_avl_info = None
                snapshot = None
            self._models["avl"] = avl_tree
            # 再次检查恢复后的中序遍历与快照是否一致（仅用于调试）
            try:
                check = self._models["avl"].get_inorder_traversal()
                print(f"[AVL RESTORE] step={self._current_avl_step} restored_snapshot={check}")
            except Exception:
                pass
            # Debug log
            try:
                print(f"[AVL HISTORY] prev -> step={self._current_avl_step} len={len(self._avl_history)} snapshot={snapshot}")
            except Exception:
                pass
            self._update_avl_history_buttons()
            self.update_view()
    
    def handle_avl_next(self):
        """处理AVL树的下一步操作"""
        if self._current_avl_step < len(self._avl_history) - 1:
            self._current_avl_step += 1
            # 从历史记录中恢复AVL树状态（兼容旧的直接存root或新的{root,info}格式）
            state = self._avl_history[self._current_avl_step]
            avl_tree = AVLTree()
            if isinstance(state, dict) and "root" in state:
                avl_tree.root = copy.deepcopy(state["root"])
                self._current_avl_info = copy.deepcopy(state.get("info"))
                snapshot = state.get("snapshot")
            else:
                avl_tree.root = copy.deepcopy(state)
                self._current_avl_info = None
                snapshot = None
            self._models["avl"] = avl_tree
            try:
                check = self._models["avl"].get_inorder_traversal()
                print(f"[AVL RESTORE] step={self._current_avl_step} restored_snapshot={check}")
            except Exception:
                pass

            try:
                print(f"[AVL HISTORY] next -> step={self._current_avl_step} len={len(self._avl_history)} snapshot={snapshot}")
            except Exception:
                pass
            self._update_avl_history_buttons()
            self.update_view()
    
    def handle_avl_history_reset(self):
        """重置AVL树的历史记录"""
        self._avl_history = []
        self._current_avl_step = -1
        self._current_avl_info = None
        self._models["avl"] = AVLTree()
        self._update_avl_history_buttons()
        self.update_view()
    
    def _update_avl_history_buttons(self):
        """更新AVL树历史操作按钮的状态"""
        self._view.avl_prev_button.setEnabled(self._current_avl_step > 0)
        self._view.avl_next_button.setEnabled(self._current_avl_step < len(self._avl_history) - 1)
        self._view.avl_history_reset_button.setEnabled(len(self._avl_history) > 0)
    
    def handle_mode_change(self):
        """处理演示模式切换：数据结构演示 <-> 算法演示"""
        # 在初始化期间可能会被多次调用，但只在初始化完成后处理
        if getattr(self, '_initializing', False):
            return
        
        # 清空视图中的所有图形内容
        try:
            self._view.clear_all_visuals()
        except Exception:
            pass
            
        is_data_struct = self._view.radio_data_structure.isChecked()
        is_algorithm = self._view.radio_algorithm.isChecked()
        
        # 获取 AI 面板及其父容器（右侧面板）
        ai_group = getattr(self._view, 'ai_group', None)
        right_panel = ai_group.parentWidget() if ai_group else None
        
        if is_data_struct:
            # 数据结构模式：显示 AI 助手
            if ai_group: ai_group.setVisible(True)
            if right_panel: right_panel.setVisible(True)

            # 切换到数据结构演示模式 - 显示结构选择面板，隐藏算法面板
            self._view.structure_group.setVisible(True)
            self._view.algorithm_group.setVisible(False)
            
            # 隐藏独立的算法选择框
            if hasattr(self._view, 'algo_select_group'):
                self._view.algo_select_group.setVisible(False)
            
            # 根据当前活跃的数据结构，恢复其对应的操作面板
            # 通过重新应用 handle_structure_change 的面板控制逻辑
            structure_name = self._active_model_name
            
            is_generic_tree = (structure_name == "generic_tree")
            is_bst_mode = (structure_name == "bst")
            is_huffman_mode = (structure_name == "huffman_tree")

            # 设置 B-树 初始讲解文本
            if structure_name == "b_tree":
                model = self._models.get("b_tree")
                t = model.t if model else 3
                min_k = t - 1
                max_k = 2 * t - 1
                self._current_btree_info = (
                    f"【B-树 规则说明】\n"
                    f"当前最小度数 t = {t}\n"
                    f"-----------------------\n"
                    f"1. 节点关键字数范围:\n"
                    f"   [{min_k} ... {max_k}]\n"
                    f"   (根节点最少1个)\n"
                    f"2. 节点满时 ({max_k}个) 分裂:\n"
                    f"   中间元素上移，\n"
                    f"   分裂成两个子节点。"
                )
            else:
                self._current_btree_info = None

            is_avl_mode = (structure_name == "avl")
            
            # 通用输入框
            if hasattr(self._view, 'value_input'):
                self._view.value_input.setVisible(not is_generic_tree and not is_huffman_mode)
            
            # 动态操作面板
            if hasattr(self._view, 'dynamic_ops_group'):
                self._view.dynamic_ops_group.setVisible(not is_generic_tree and not is_huffman_mode)
            
            # 顺序表/链表分步演示
            if hasattr(self._view, 'seq_step_group'):
                self._view.seq_step_group.setVisible(structure_name in ("sequential_list", "linked_list"))
            
            # 文件操作
            if hasattr(self._view, 'file_ops_group'):
                self._view.file_ops_group.setVisible(True)
            
            # 各自模式的专属UI
            if hasattr(self._view, 'build_tree_group'):
                self._view.build_tree_group.setVisible(is_generic_tree)
            if hasattr(self._view, 'search_ops_group'):
                self._view.search_ops_group.setVisible(is_bst_mode)
            if hasattr(self._view, 'delete_step_group'):
                self._view.delete_step_group.setVisible(is_bst_mode)
            if hasattr(self._view, 'bst_build_group'):
                self._view.bst_build_group.setVisible(is_bst_mode)
            if hasattr(self._view, 'huffman_group'):
                self._view.huffman_group.setVisible(is_huffman_mode)
            if hasattr(self._view, 'avl_history_group'):
                self._view.avl_history_group.setVisible(is_avl_mode)

            # 只有当当前结构是 b_tree 时才显示参数设置
            if hasattr(self._view, 'b_tree_group'):
                self._view.b_tree_group.setVisible(structure_name == "b_tree")


            if hasattr(self._view, 'stack_ops_group'):
                self._view.stack_ops_group.setVisible(structure_name == "stack")
                
        elif is_algorithm:
            if ai_group: ai_group.setVisible(False)
            if right_panel: right_panel.setVisible(False) # 隐藏父容器以回收空间
            # 切换到算法演示模式 - 隐藏数据结构相关面板，只显示算法面板
            self._view.structure_group.setVisible(False)
            self._view.algorithm_group.setVisible(True)
            
            # 显示独立的算法选择框 
            if hasattr(self._view, 'algo_select_group'):
                self._view.algo_select_group.setVisible(True)
            
            # 隐藏所有数据结构操作相关的面板
            if hasattr(self._view, 'value_input'):
                self._view.value_input.setVisible(False)
            if hasattr(self._view, 'dynamic_ops_group'):
                self._view.dynamic_ops_group.setVisible(False)
            if hasattr(self._view, 'delete_step_group'):
                self._view.delete_step_group.setVisible(False)
            if hasattr(self._view, 'file_ops_group'):
                self._view.file_ops_group.setVisible(False)
            if hasattr(self._view, 'search_ops_group'):
                self._view.search_ops_group.setVisible(False)
            if hasattr(self._view, 'stack_ops_group'):
                self._view.stack_ops_group.setVisible(False)
            if hasattr(self._view, 'bst_build_group'):
                self._view.bst_build_group.setVisible(False)
            if hasattr(self._view, 'avl_history_group'):
                self._view.avl_history_group.setVisible(False)
            if hasattr(self._view, 'huffman_group'):
                self._view.huffman_group.setVisible(False)
            if hasattr(self._view, 'build_tree_group'):
                self._view.build_tree_group.setVisible(False)
            if hasattr(self._view, 'seq_step_group'):
                self._view.seq_step_group.setVisible(False)
            # 在算法模式下强制隐藏 B-树设置
            if hasattr(self._view, 'b_tree_group'):
                self._view.b_tree_group.setVisible(False)
    
    def handle_structure_change(self, structure_name):
        prev_active = self._active_model_name
        radio = getattr(self._view, f"radio_{structure_name}")
        if radio.isChecked():

            if not getattr(self, '_suppress_structure_side_effects', False):
                self.handle_search_reset() 
                self.handle_build_reset()
                self.handle_huffman_build_reset() # 重置哈夫曼树状态
            if self._active_model_name == "avl":
                self.handle_avl_history_reset()  # 如果切换出AVL树模式，重置其历史
            self._active_model_name = structure_name
            
            is_generic_tree = (structure_name == "generic_tree")
            is_bst_mode = (structure_name == "bst")
            is_huffman_mode = (structure_name == "huffman_tree")

            # 控制通用输入框的可见性
            self._view.value_input.setVisible(not is_generic_tree and not is_huffman_mode)

            # 动态操作
            is_avl_mode = (structure_name == "avl")
            self._view.dynamic_ops_group.setVisible(not is_generic_tree and not is_huffman_mode)
            # 顺序表分步面板仅在顺序表模式下显示
            try:
                # 顺序表和链表都支持分步查找/删除，显示相同的控制面板
                self._view.seq_step_group.setVisible(structure_name in ("sequential_list", "linked_list"))
                # 根据当前模式调整该分步面板的标题（顺序表 / 链表）
                if structure_name == "linked_list":
                    self._view.seq_step_group.setTitle("链表 分步演示")
                else:
                    # 默认展示为顺序表标题（包括 sequential_list 模式）
                    self._view.seq_step_group.setTitle("顺序表 分步演示")
            except Exception:
                pass
            
            # 各自模式的专属UI
            self._view.build_tree_group.setVisible(is_generic_tree)
            self._view.search_ops_group.setVisible(is_bst_mode)
            self._view.delete_step_group.setVisible(is_bst_mode)
            self._view.bst_build_group.setVisible(is_bst_mode) # 控制BST构建面板的可见性
            self._view.huffman_group.setVisible(is_huffman_mode)
            self._view.avl_history_group.setVisible(is_avl_mode)
            # 控制 B-树 设置面板可见性
            is_btree_mode = (structure_name == "b_tree")
            if hasattr(self._view, 'b_tree_group'):
                try:
                    self._view.b_tree_group.setVisible(is_btree_mode)
                except Exception:
                    pass
            self._update_avl_history_buttons()
            # 显示/隐藏栈操作面板
            try:
                is_stack_mode = (structure_name == "stack")
                self._view.stack_ops_group.setVisible(is_stack_mode)
                # 如果进入栈模式，则隐藏与分步演示相关的其他控制面板（它们在栈模式下无效）
                if is_stack_mode:
                    try:
                        self._view.dynamic_ops_group.setVisible(False)
                        self._view.seq_step_group.setVisible(False)
                        self._view.delete_step_group.setVisible(False)
                        self._view.search_ops_group.setVisible(False)
                        self._view.bst_build_group.setVisible(False)
                        self._view.huffman_group.setVisible(False)
                        self._view.avl_history_group.setVisible(False)
                        self._view.build_tree_group.setVisible(False)
                        # 保险起见在栈模式下也显式隐藏 B-树面板
                        if hasattr(self._view, 'b_tree_group'):
                            self._view.b_tree_group.setVisible(False)

                    except Exception:
                        pass
            except Exception:
                pass

            try:
                if prev_active != structure_name and not getattr(self, '_suppress_structure_side_effects', False):
                    if hasattr(self._view, 'clear_all_visuals'):
                        try:
                            self._view.clear_all_visuals()
                        except Exception:
                            pass
                    try:
                        if hasattr(self._view, 'clear_cached_right_box'):
                            try:
                                self._view.clear_cached_right_box()
                            except Exception:
                                pass
                    except Exception:
                        pass
                    try:
                        try:
                            self._view.scene.clear()
                        except Exception:
                            pass
                    except Exception:
                        pass
                    try:
                        if hasattr(self._view, '_cached_info_item') and self._view._cached_info_item is not None:
                            try:
                                self._view.scene.removeItem(self._view._cached_info_item)
                            except Exception:
                                pass
                            self._view._cached_info_item = None
                    except Exception:
                        pass
                    try:
                        if hasattr(self._view, '_cached_info_text'):
                            self._view._cached_info_text = None
                    except Exception:
                        pass
                    try:
                        if prev_active in self._models:
                            if prev_active == 'stack':
                                self._models['stack'] = SequentialStack()
                            elif prev_active == 'sequential_list':
                                self._models['sequential_list'] = SequentialList()
                            elif prev_active == 'linked_list':
                                self._models['linked_list'] = LinkedList()
                            elif prev_active == 'bst':
                                self._models['bst'] = BinarySearchTree()
                            elif prev_active == 'avl':
                                self._models['avl'] = AVLTree()
                            elif prev_active == 'generic_tree':
                                self._models['generic_tree'] = GenericBinaryTree()
                            elif prev_active == 'huffman_tree':
                                self._models['huffman_tree'] = None
                    except Exception:
                        pass
            except Exception:
                pass

            self.update_view()

    def handle_bst_build(self):
        """处理从序列构建BST的请求"""
        if self._active_model_name != "bst": return
        
        input_str = self._view.bst_build_input.text()
        if not input_str: return

        try:
            values = [int(x.strip()) for x in input_str.split(',')]
            
            # 创建新的BST模型实例
            bst_model = BinarySearchTree()
            for value in values:
                bst_model.insert(value)
            
            self._models["bst"] = bst_model
            self.update_view()
        except ValueError:
            try:
                self._view.display_info_text("构建失败：输入必须为整数序列，用逗号分隔。")
            except Exception:
                pass
            return

    # Stack 操作处理
    def handle_stack_push(self):
        # 只在 stack 模式下有效
        if self._active_model_name != 'stack':
            return
        val_str = self._view.value_input.text()
        if val_str is None or val_str.strip() == "":
            try:
                self._view.display_info_text("请输入入栈值后再按 入栈。", origin='stack')
            except Exception:
                pass
            return
        # 入栈（把文本作为字符串存储，保持通用）
        try:
            stack_model = self._models['stack']
            # 记录入栈前的长度以便确定新元素的索引
            before_len = stack_model.get_length()
            stack_model.push(val_str)
            self._view.display_info_text(f"已入栈: {val_str}（推入栈顶）", origin='stack')
            # 设置短暂可视化：蓝圈包围新 push 的元素（索引为 before_len）
            self._stack_viz = {"pushed_index": before_len}
            self.update_view()
            # 在短延时后自动清除可视化提示
            try:
                QTimer.singleShot(self._auto_reset_delay_ms, self._clear_stack_viz)
            except Exception:
                pass
        except Exception as e:
            try:
                self._view.display_info_text(f"入栈失败: {e}", origin='stack')
            except Exception:
                pass

    def handle_stack_pop(self):
        if self._active_model_name != 'stack':
            return
        try:
            stack_model = self._models['stack']
            before_len = stack_model.get_length()
            popped = stack_model.pop()
            if popped is None:
                self._view.display_info_text("出栈失败：栈为空（underflow）。", origin='stack')
            else:
                self._view.display_info_text(f"已出栈: {popped}", origin='stack')
                # 记录被弹出的值与原先的索引，便于在视图中绘制被弹出的方框
                self._stack_viz = {"popped_value": popped, "popped_from_index": before_len - 1}
                # 更新视图（注意此时栈已减一，draw_stack 会绘制当前栈，同时根据 viz 绘制 popped 方框）
                self.update_view()
                try:
                    QTimer.singleShot(self._auto_reset_delay_ms, self._clear_stack_viz)
                except Exception:
                    pass
        except Exception as e:
            try:
                self._view.display_info_text(f"出栈出错: {e}", origin='stack')
            except Exception:
                pass
            self.update_view()

    def handle_stack_top(self):
        """处理查看栈顶的操作 (无需输入参数)"""
        if self._active_model_name != 'stack':
            return
        
        try:
            stack_model = self._models['stack']
            # 尝试获取栈顶元素 (支持 top 或 peek 方法)
            top_val = None
            if hasattr(stack_model, 'top'):
                top_val = stack_model.top()
            elif hasattr(stack_model, 'peek'):
                top_val = stack_model.peek()
            
            if top_val is None:
                try:
                    self._view.display_info_text("栈为空，没有栈顶元素。", origin='stack')
                except Exception:
                    pass
            else:
                try:
                    self._view.display_info_text(f"栈顶元素: {top_val}", origin='stack')
                except Exception:
                    pass
                # 设置短暂可视化：高亮栈顶元素（假设视图层支持 highlight_top）
                self._stack_viz = {"highlight_top": True}
                self.update_view()
                
                # 1.5秒后自动清除高亮
                try:
                    QTimer.singleShot(self._auto_reset_delay_ms, self._clear_stack_viz)
                except Exception:
                    pass
        except Exception as e:
            try:
                self._view.display_info_text(f"查询栈顶出错: {e}", origin='stack')
            except Exception:
                pass

    def _clear_stack_viz(self):
        """清除栈的短暂可视化提示并刷新视图。"""
        try:
            self._stack_viz = None
            self.update_view()
        except Exception:
            pass


    def handle_bst_reset_tree(self):
        """清空整个BST模型并刷新视图。"""
        try:
            # 重建一个新的空BST实例
            self._models["bst"] = BinarySearchTree()

            # 清除与BST相关的临时状态（查找、删除等）
            self._search_path_iterator = None
            self._highlighted_node_key = None
            self._current_search_info = None
            self._current_search_value = None

            self._delete_path_iterator = None
            self._current_delete_info = None
            self._delete_history = []
            self._current_delete_step = -1

            # 更新视图以反映空树
            self.update_view()
        except Exception:
            # 保持容错，避免因UI未就绪而抛出异常
            pass


    def handle_btree_reset_degree(self):
        """
        处理 B-树 重置阶数的请求
        """
        if self._active_model_name != "b_tree":
            return
        try:
            # 获取用户设置的 t 值
            new_t = self._view.btree_degree_spin.value()

            # 1. 重新初始化 B树 模型
            self._models["b_tree"] = BTree(t=new_t)

            # 2. 清空画布
            try:
                self._view.scene.clear()
            except Exception:
                pass
            
            # 3. 彻底清除视图层的文本缓存（这是解决“幽灵文字”的关键）
            if hasattr(self._view, '_cached_info_text'):
                try:
                    self._view._cached_info_text = None
                except Exception:
                    pass
            if hasattr(self._view, 'clear_cached_right_box'):
                try:
                    self._view.clear_cached_right_box()
                except Exception:
                    pass

            # 4. 设置新的常驻状态文本（显示新规则，而不是“重置成功”）
            min_k = new_t - 1
            max_k = 2 * new_t - 1
            
            # 直接将 info 更新为规则说明
            self._current_btree_info = (
                f"【B-树参数已更新】\n"
                f"当前最小度数 t = {new_t}\n"
                f"-----------------------\n"
                f"1. 关键字数范围:\n"
                f"   [{min_k} ... {max_k}]\n"
                f"2. 超过 {max_k} 个时:\n"
                f"   节点将分裂"
            )

            # 5. 显示 B-树阶数的图片说明（辅助）
            try:
                if hasattr(self._view, 'show_b_tree_info'):
                    self._view.show_b_tree_info(new_t)
            except Exception:
                pass
            
            # 6. 刷新视图
            try:
                self.update_view()
            except Exception:
                pass
            
        except Exception as e:
            print(f"B-Tree reset error: {e}")


    # AI 处理逻辑
    def handle_ai_request(self):
        user_text = self._view.ai_input.text()
        if not user_text:
            return

        self._view.ai_chat_display.append(f"<b>You:</b> {user_text}")
        self._view.ai_input.clear()
        self._view.ai_send_button.setEnabled(False)

        # 改 System Prompt：加入 get/pop，并区分删除方式
        system_prompt = """
        You are an intelligent controller for a Data Structure Visualization software.
        Current Active Structure: {active}.

        Your Goal: Convert user natural language requests into a sequence of JSON commands.

        CRITICAL LOGIC RULES:
        1. Structure Switching: If the user mentions a specific data structure, output "switch_structure" FIRST.
        2. Value Extraction: 
            - Huffman Tree: "char:weight".
            - Others: Integers.
        3. Operations:
            - **Stack Top**: Output {"action": "get", "type": "top"}. Do NOT use "search" for stack top.
            - **Stack Pop**: Output {"action": "pop"}. (No value needed)
            - **Delete by Value**: e.g. "Delete 5" -> {"action": "delete", "type": "value", "value": 5}.
            - **Delete by Index**: e.g. "Delete index 2" -> {"action": "delete", "type": "index", "value": 2}.
        4. Multi-step: Switch first, then operate.

        Available Structures: sequential_list, linked_list, stack, bst, avl, generic_tree, huffman_tree, b_tree.

        Examples:
        User: "Delete 5"
        Output: [{"action": "delete", "type": "value", "value": 5}]

        User: "Remove the element at index 1"
        Output: [{"action": "delete", "type": "index", "value": 1}]
        """.replace("{active}", self._active_model_name)

        # 发送到后台线程处理 AI 请求（保持原有异常处理逻辑）
        try:
            threading.Thread(target=self._ai_worker, args=(system_prompt, user_text), daemon=True).start()
        except Exception as e:
            try:
                self._view.ai_chat_display.append(f"<font color='red'>Error starting AI thread: {e}</font>")
                self._view.ai_send_button.setEnabled(True)
            except Exception:
                pass


    def _ai_worker(self, system_prompt, user_text):
        print("[DEBUG] 线程启动，准备请求 AI")
        try:
            if not self.ai_client:
                raise Exception("AI 客户端未初始化 (ai_client is None)")

            try:
                base_url = getattr(self.ai_client, 'base_url', '<unknown>')
            except Exception:
                base_url = '<unknown>'
            print(f"[DEBUG] 正在连接 LM Studio: {base_url}")
            
            # 发送请求，增加超时防止无限等待
            completion = self.ai_client.chat.completions.create(
                model="local-model",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_text}
                ],
                temperature=0.7,
                timeout=60.0
            )
            
            print("[DEBUG] 收到 LM Studio 回复")
            response_content = completion.choices[0].message.content
            print(f"[DEBUG] 回复内容: {response_content[:50]}...")

            # 使用信号发射将回复发送回主线程处理（线程安全）
            try:
                self.ai_response_received.emit(response_content)
            except Exception:
                # 作为回退，仍然使用 QTimer 将回调转回主线程
                from PySide6.QtCore import QTimer
                QTimer.singleShot(0, lambda: self._process_ai_response(response_content))

        except Exception as e:
            print(f"[DEBUG] 发生错误: {e}")
            from PySide6.QtCore import QTimer
            error_msg = str(e)
            # 将错误处理也安排回主线程执行
            try:
                QTimer.singleShot(0, lambda: self._handle_ai_error(error_msg))
            except Exception:
                pass


    def _process_ai_response(self, response_text):
        self._view.ai_send_button.setEnabled(True)
        print(f"[DEBUG] 原始回复内容: {response_text}")
        
        actions = []
        
        # 阶段1: 尝试直接解析标准 JSON (结构化输出模式) 
        try:
            parsed = json.loads(response_text)
            # 兼容模型可能返回单个对象而不是列表的情况
            if isinstance(parsed, dict):
                actions = [parsed]
            elif isinstance(parsed, list):
                actions = parsed
            
            print(f"[DEBUG] 成功解析标准 JSON: {len(actions)} 条指令")
            
        except json.JSONDecodeError:
            # 阶段2: 解析失败，回退到“手动提取”模式
            print("[DEBUG] 标准 JSON 解析失败，尝试手动提取...")
            decoder = json.JSONDecoder()
            pos = 0
            while pos < len(response_text):
                # 跳过非 '{' 字符
                if response_text[pos] != '{':
                    pos += 1
                    continue
                try:
                    obj, idx = decoder.raw_decode(response_text[pos:])
                    actions.append(obj)
                    pos += idx
                except json.JSONDecodeError:
                    pos += 1

        if not actions:
            # 如果什么都没提取到，直接显示原文
            self._view.ai_chat_display.append(f"<b>AI:</b> {response_text}")
            return

        # 阶段3: 执行指令 
        try:
            for act in actions:
                action_type = act.get("action")
                
                if action_type == "switch_structure":
                    struct = act.get("structure")
                    self._view.ai_chat_display.append(f"<i>AI: 切换到 {struct}...</i>")
                    if hasattr(self._view, f"radio_{struct}"):
                        getattr(self._view, f"radio_{struct}").setChecked(True)
                        from PySide6.QtCore import QCoreApplication
                        QCoreApplication.processEvents()
                
                elif action_type == "insert":
                    values = act.get("values", [])
                    if isinstance(values, int) or isinstance(values, str):
                        values = [values]

                    self._view.ai_chat_display.append(f"<i>AI: 插入 {values}...</i>")

                    # 如果是哈夫曼树，批量处理所有插入值，一次性更新
                    if self._active_model_name == "huffman_tree":
                        try:
                            current_text = self._view.huffman_input.text().strip()
                            items = []
                            if current_text:
                                items.append(current_text)
                            
                            for val in values:
                                val_str = str(val)
                                # 格式化处理
                                if ":" not in val_str:
                                    new_item = f"{val_str}:{val_str}"
                                else:
                                    new_item = val_str
                                items.append(new_item)
                            
                            # 用逗号连接
                            new_full_text = ", ".join(items)
                            self._view.huffman_input.setText(new_full_text)
                            
                            # 触发绘制
                            self.handle_huffman_draw()
                            
                            self._view.display_info_text(f"已批量添加哈夫曼节点: {values}")
                        except Exception as e:
                            print(f"哈夫曼插入失败: {e}")

                    else:
                        # 其他结构（BST, 顺序表等）逐个处理
                        for val in values:
                            try:
                                val_int = int(val)
                                
                                if self._active_model_name in ["sequential_list", "linked_list"]:
                                    model = self._models[self._active_model_name]
                                    model.insert(model.get_length(), val_int)
                                    self.update_view()
                                else:
                                    self._view.value_input.setText(str(val_int))
                                    self.handle_insert()
                                
                                from PySide6.QtCore import QCoreApplication
                                QCoreApplication.processEvents()
                            except Exception as e:
                                print(f"插入值 {val} 失败: {e}")

                # 处理 Pop 指令 
                elif action_type == "pop":
                    try:
                        self._view.ai_chat_display.append(f"<i>AI: 执行出栈...</i>")
                    except Exception:
                        pass
                    try:
                        # 使用专门的栈弹出处理以获得更好的可视化与提示
                        self.handle_stack_pop()
                    except Exception:
                        pass

                elif action_type == "delete":
                    val = act.get("value")
                    del_type = act.get("type")

                    # 按索引删除
                    if del_type == "index":
                        try:
                            idx = int(val)
                            try:
                                self._view.ai_chat_display.append(f"<i>AI: 删除索引 {idx}...</i>")
                            except Exception:
                                pass
                            try:
                                self.handle_delete_by_index(idx)
                            except Exception:
                                pass
                        except Exception:
                            # 无效索引值，回退为按值删除
                            try:
                                self._view.ai_chat_display.append(f"<i>AI: 删除 {val}...</i>")
                            except Exception:
                                pass
                            try:
                                self._view.value_input.setText(str(val))
                                self.handle_delete()
                            except Exception:
                                pass

                    # 默认按值删除
                    else:
                        try:
                            self._view.ai_chat_display.append(f"<i>AI: 删除值 {val}...</i>")
                        except Exception:
                            pass
                        try:
                            self._view.value_input.setText(str(val))
                            self.handle_delete()
                        except Exception:
                            pass

                elif action_type == "search":
                    val = act.get("value")
                    # 如果模型仍发送旧的 "search" 指令来查询栈顶，兼容为 get top
                    try:
                        sval = str(val).strip().lower()
                    except Exception:
                        sval = None

                    if sval in ("top", "stack top") and self._active_model_name == "stack":
                        try:
                            self._view.ai_chat_display.append(f"<i>AI: 查看栈顶 (兼容)...</i>")
                        except Exception:
                            pass
                        try:
                            self.handle_stack_top()
                        except Exception:
                            pass
                    else:
                        try:
                            self._view.ai_chat_display.append(f"<i>AI: 查找 {val}...</i>")
                        except Exception:
                            pass
                        try:
                            self._view.value_input.setText(str(val))
                            self.handle_search_start()
                        except Exception:
                            pass
                
                # 处理 Get/Peek 指令
                elif action_type == "get":
                    get_type = act.get("type")

                    # 1. 查看栈顶 — 使用专门的 get/top 指令，不要使用 search
                    if get_type == "top":
                        try:
                            self._view.ai_chat_display.append(f"<i>AI: 查看栈顶...</i>")
                        except Exception:
                            pass
                        try:
                            # 复用已有的栈顶查看实现（与 UI 按钮行为一致）
                            self.handle_stack_top()
                        except Exception:
                            pass

                    # 2. 查看特定索引 (用于顺序表/链表)
                    elif get_type == "index":
                        val = act.get("value")
                        try:
                            idx = int(val)
                            try:
                                self._view.ai_chat_display.append(f"<i>AI: 查看索引 {idx}...</i>")
                            except Exception:
                                pass
                            try:
                                self.handle_get_by_index(idx)
                            except Exception:
                                pass
                        except Exception:
                            # 无效索引值，忽略该指令
                            pass

                elif action_type == "explain":
                    self._view.ai_chat_display.append(f"<b>AI:</b> {act.get('text')}")
        except Exception as e:
            print(f"处理指令出错: {e}")
            self._view.ai_chat_display.append(f"<b>AI Error:</b> 无法解析指令")
    
    def _handle_ai_error(self, error_msg):
        """在主线程中处理 AI 请求错误：显示消息并恢复发送按钮。"""
        try:
            self._view.ai_chat_display.append(f"<font color='red'>Error: {error_msg}</font>")
            self._view.ai_send_button.setEnabled(True)
        except Exception:
            pass


    def _build_random_tree_and_traversals(self, node_count=None):
        """
        构建一个随机二叉树并返回
        """
        if node_count is None:
            node_count = random.randint(3, 12)

        values = random.sample(range(1, 201), node_count)
        nodes = [TreeNode(v) for v in values]

        # 以层序方式构造树：随机分配父节点的空位
        available = [nodes[0]]
        for node in nodes[1:]:
            # 选择一个有空位的父节点
            parent = random.choice(available)
            # 随机选择左右，如果已被占用则尝试另一个或换父节点
            for _ in range(10):
                side = random.choice(['left', 'right'])
                if getattr(parent, side) is None:
                    setattr(parent, side, node)
                    break
                else:
                    # 尝试切换侧或选择新的父
                    if getattr(parent, 'left') is None:
                        parent.left = node
                        break
                    if getattr(parent, 'right') is None:
                        parent.right = node
                        break
                    parent = random.choice(available)
            # 新节点也有空位，加入可用列表
            available.append(node)
            # 如果父节点左右都被占用，从可用列表移除
            if parent.left and parent.right:
                try:
                    available.remove(parent)
                except ValueError:
                    pass

        root = nodes[0]

        # 计算遍历序列
        preorder_list = []
        inorder_list = []
        postorder_list = []

        def _pre(n):
            if not n: return
            preorder_list.append(n.key)
            _pre(n.left)
            _pre(n.right)

        def _in(n):
            if not n: return
            _in(n.left)
            inorder_list.append(n.key)
            _in(n.right)

        def _post(n):
            if not n: return
            _post(n.left)
            _post(n.right)
            postorder_list.append(n.key)

        _pre(root); _in(root); _post(root)

        # 层序（包含 null 占位），直到最后一个非 None
        from collections import deque
        q = deque([root])
        level = []
        while q:
            n = q.popleft()
            if n is None:
                level.append(None)
                continue
            level.append(n.key)
            # 将子节点（可能为 None）入队
            q.append(n.left if getattr(n, 'left', None) else None)
            q.append(n.right if getattr(n, 'right', None) else None)
        # 去掉尾部多余的 None
        while level and level[-1] is None:
            level.pop()

        return root, preorder_list, inorder_list, postorder_list, level

    def handle_pre_in_random(self):
        try:
            _, preorder_list, inorder_list, _, _ = self._build_random_tree_and_traversals()
            self._view.preorder_input.setText(",".join(str(x) for x in preorder_list))
            self._view.inorder_input_pre.setText(",".join(str(x) for x in inorder_list))
        except Exception:
            pass

    def handle_post_in_random(self):
        try:
            _, _, inorder_list, postorder_list, _ = self._build_random_tree_and_traversals()
            self._view.postorder_input.setText(",".join(str(x) for x in postorder_list))
            self._view.inorder_input_post.setText(",".join(str(x) for x in inorder_list))
        except Exception:
            pass

    def handle_level_random(self):
        try:
            _, _, _, _, level_list = self._build_random_tree_and_traversals()
            # 将 None 转为 'null' 字符串以匹配视图占位示例
            parts = [str(x) if x is not None else 'null' for x in level_list]
            self._view.levelorder_input.setText(",".join(parts))
        except Exception:
            pass


    def handle_search_start(self):
        """
        处理BST查找的开始操作
        """
        if self._active_model_name != "bst": return
        
        self.handle_search_reset() # 开始新的查找前先重置
        active_model = self._models["bst"]
        value_str = self._view.value_input.text()
        if not value_str: return
        try: value = int(value_str)
        except ValueError: return
        
        # 记录当前要查找的值，并从模型获取查找路径的生成器
        self._current_search_value = value
        self._current_search_info = None
        self._search_path_iterator = active_model.search_path(value)
        
        # 启用/禁用按钮进入“查找模式”
        self._view.next_step_button.setEnabled(True)
        self._view.reset_button.setEnabled(True)
        self._view.insert_button.setEnabled(False)
        self._view.delete_button.setEnabled(False)
        
        # 自动走第一步
        self.handle_search_next()

    

    def handle_search_next(self):
        """
        处理BST查找的下一步操作
        """
        if self._search_path_iterator:
            try:
                # 从生成器中获取下一个节点
                next_node = next(self._search_path_iterator)
                self._highlighted_node_key = next_node.key

                # 构造更有信息性的文字说明
                try:
                    target = self._current_search_value
                    if next_node.key == target:
                        text = f"找到目标 {target} (当前节点 {next_node.key})。"
                    elif target < next_node.key:
                        text = f"比较: 当前节点 {next_node.key} > 目标 {target} → 向左子树继续查找。"
                    else:
                        text = f"比较: 当前节点 {next_node.key} < 目标 {target} → 向右子树继续查找。"
                except Exception:
                    text = f"访问节点 {next_node.key}。"

                # 保存为当前查找信息，优先在视图中显示
                self._current_search_info = {"highlight_key": self._highlighted_node_key, "text": text}
                self.update_view()
            except StopIteration:
                # 生成器已耗尽，说明查找结束
                self._view.next_step_button.setEnabled(False)
                # 在结束时显示完成信息
                if hasattr(self, '_current_search_value'):
                    self._current_search_info = {"highlight_key": None, "text": f"查找结束: 未找到 {self._current_search_value} 或已完成查找。"}
                self.update_view()

    # 处理重置
    def handle_search_reset(self):
        self._search_path_iterator = None
        self._highlighted_node_key = None
        # 清除搜索相关的信息
        self._current_search_info = None
        self._current_search_value = None
        
        # 恢复UI状态
        self._view.next_step_button.setEnabled(False)
        self._view.reset_button.setEnabled(False)
        self._view.insert_button.setEnabled(True)
        self._view.delete_button.setEnabled(True)
        
        self.update_view()

    def handle_huffman_build_start(self):
        self.handle_huffman_build_reset()
        input_str = self._view.huffman_input.text()
        if not input_str: return

        frequencies = {}
        try:
            pairs = input_str.split(',')
            for pair in pairs:
                if ':' not in pair: continue
                char, weight_str = pair.split(':', 1)
                char = char.strip()
                weight = int(weight_str.strip())
                if not char: continue
                frequencies[char] = weight
            
            if not frequencies: raise ValueError("输入数据无效或为空。")

            # 创建模型实例并获取生成器
            huffman_model = HuffmanTree()
            self._models["huffman_tree"] = huffman_model
            self._huffman_build_iterator = huffman_model.build_step_by_step(frequencies)
            self._huffman_build_history = []
            self._current_huffman_build_step = -1

            # 更新UI状态
            self._view.huffman_start_button.setEnabled(False)
            self._view.huffman_next_step_button.setEnabled(True)
            self._view.huffman_reset_button.setEnabled(True)
            self.handle_huffman_build_next()

        except (ValueError, IndexError) as e:
            self._current_huffman_build_state = {"text": f"输入错误: {e}"}
            self.update_view()

    def handle_huffman_build_next(self):
        # 如果可以从历史记录中前进
        if self._current_huffman_build_step < len(self._huffman_build_history) - 1:
            self._current_huffman_build_step += 1
            self._current_huffman_build_state = self._huffman_build_history[self._current_huffman_build_step]
            self.update_view()
            self._update_huffman_buttons_state()
            return

        # 否则，从生成器获取新步骤
        if self._huffman_build_iterator:
            try:
                state = next(self._huffman_build_iterator)
                # 深拷贝状态以存储历史
                state_copy = copy.deepcopy(state)
                self._huffman_build_history.append(state_copy)
                self._current_huffman_build_step += 1
                
                self._current_huffman_build_state = state
                # 如果是最后一步，更新模型的主树根
                if state.get("tree"):
                    self._models["huffman_tree"].root = state["tree"]
                self.update_view()
            except StopIteration:
                self._view.huffman_next_step_button.setEnabled(False)
            self._update_huffman_buttons_state()

    def handle_huffman_build_prev(self):
        if self._current_huffman_build_step > 0:
            self._current_huffman_build_step -= 1
            self._current_huffman_build_state = self._huffman_build_history[self._current_huffman_build_step]
            self.update_view()
            self._update_huffman_buttons_state()

    def handle_huffman_build_reset(self):
        self._huffman_build_iterator = None
        self._current_huffman_build_state = None
        self._huffman_build_history = []
        self._current_huffman_build_step = -1
        if "huffman_tree" in self._models:
            self._models["huffman_tree"] = None
        
        self._view.huffman_start_button.setEnabled(True)
        self._view.huffman_prev_step_button.setEnabled(False)
        self._view.huffman_next_step_button.setEnabled(False)
        self._view.huffman_reset_button.setEnabled(False)
        
        if self._active_model_name == "huffman_tree":
            self.update_view()

    def _update_huffman_buttons_state(self):
        self._view.huffman_prev_step_button.setEnabled(self._current_huffman_build_step > 0)
        
        is_iterator_exhausted = self._current_huffman_build_step == len(self._huffman_build_history) - 1 and self._huffman_build_iterator is None
        self._view.huffman_next_step_button.setEnabled(not is_iterator_exhausted)

    def handle_build_tree(self):
        """处理构建普通二叉树的事件"""
        model = self._models["generic_tree"]
        
        preorder_str = self._view.preorder_input.text()
        inorder_pre_str = self._view.inorder_input_pre.text()

        postorder_str = self._view.postorder_input.text()
        inorder_post_str = self._view.inorder_input_post.text()
        
        levelorder_str = self._view.levelorder_input.text()
        
        info_text = "" # 用于存储要显示的信息

        try:
            if preorder_str and inorder_pre_str:
                pre = [int(x.strip()) for x in preorder_str.split(',')]
                ino = [int(x.strip()) for x in inorder_pre_str.split(',')]
                if len(pre) != len(ino) or len(set(pre)) != len(ino):
                    raise ValueError("前序和中序遍历的元素不匹配或有重复")
                model.build_from_pre_in(pre, ino)
                # 准备要显示的信息，并清空输入框
                info_text = f"构建来源: DFT\n - 前序序列: [ {preorder_str} ]\n- 中序序列: [ {inorder_pre_str} ]"
                self._view.preorder_input.clear()
                self._view.inorder_input_pre.clear()

            elif postorder_str and inorder_post_str:
                post = [int(x.strip()) for x in postorder_str.split(',')]
                ino = [int(x.strip()) for x in inorder_post_str.split(',')]
                if len(post) != len(ino) or len(set(post)) != len(ino):
                    raise ValueError("后序和中序遍历的元素不匹配或有重复")
                model.build_from_post_in(post, ino)
                # 准备要显示的信息，并清空输入框
                info_text = f"构建来源: DFT\n - 前序序列: [ {inorder_post_str} ]\n- 后序序列: [ {postorder_str} ]"
                self._view.postorder_input.clear()
                self._view.inorder_input_post.clear()

            elif levelorder_str:
                parts = [x.strip() for x in levelorder_str.split(',')]
                level = [int(p) if p != 'null' else None for p in parts]
                model.build_from_level_order(level)
                # 准备要显示的信息，并清空输入框
                info_text = f"构建来源: BFT\n - 遍历序列: [ {levelorder_str} ]"
                self._view.levelorder_input.clear()
            else:
                print("请输入有效的遍历序列组合")
                return
        except (ValueError, KeyError, IndexError) as e:
            print(f"构建失败: {e}. 请检查输入序列是否合法且匹配。")
            model.root = None
            self.update_view()
            self._view.display_info_text(f"构建失败: {e}")
            return
            
        # 成功构建后，先画树，再在顶部添加信息
        self.update_view()
        if info_text:
            self._view.display_info_text(info_text)

    def handle_build_start(self):
        model = self._models["generic_tree"]
        iterator = None
        
        preorder_str = self._view.preorder_input.text()
        inorder_pre_str = self._view.inorder_input_pre.text()
        postorder_str = self._view.postorder_input.text()
        inorder_post_str = self._view.inorder_input_post.text()
        levelorder_str = self._view.levelorder_input.text()

        try:
            if preorder_str and inorder_pre_str:
                pre = [int(x.strip()) for x in preorder_str.split(',')]
                ino = [int(x.strip()) for x in inorder_pre_str.split(',')]
                iterator = model.build_from_pre_in(pre, ino)
            elif postorder_str and inorder_post_str:
                post = [int(x.strip()) for x in postorder_str.split(',')]
                ino = [int(x.strip()) for x in inorder_post_str.split(',')]
                iterator = model.build_from_post_in(post, ino)
            elif levelorder_str:
                parts = [x.strip() for x in levelorder_str.split(',')]
                level = [int(p) if p != 'null' else None for p in parts]
                iterator = model.build_from_level_order(level)
        except (ValueError, KeyError, IndexError) as e:
            self._current_build_info = {"text": f"输入错误: {e}"}
            self.update_view()
            return

        if iterator:
            self._build_iterator = iterator
            self._view.start_build_button.setEnabled(False)
            self._view.next_build_step_button.setEnabled(True)
            self._view.reset_build_button.setEnabled(True)
            self.handle_build_next()

    def handle_build_next(self):
        if self._build_iterator:
            try:
                state = next(self._build_iterator)
                self._models["generic_tree"].root = state["tree"]
                self._current_build_info = state["info"]
                self.update_view()
            except StopIteration:
                self._current_build_info['text'] = "构建完成！"
                self.update_view()
                self._view.next_build_step_button.setEnabled(False)

    def handle_build_reset(self):
        self._build_iterator = None
        self._current_build_info = None
        if "generic_tree" in self._models:
            self._models["generic_tree"].root = None
        # 清空普通二叉树构建面板的文本输入（如果存在）
        try:
            if hasattr(self._view, 'preorder_input'):
                self._view.preorder_input.clear()
            if hasattr(self._view, 'inorder_input_pre'):
                self._view.inorder_input_pre.clear()
            if hasattr(self._view, 'postorder_input'):
                self._view.postorder_input.clear()
            if hasattr(self._view, 'inorder_input_post'):
                self._view.inorder_input_post.clear()
            if hasattr(self._view, 'levelorder_input'):
                self._view.levelorder_input.clear()
        except Exception:
            # 容错：若视图还未完全初始化则忽略
            pass

        self._view.start_build_button.setEnabled(True)
        self._view.next_build_step_button.setEnabled(False)
        self._view.reset_build_button.setEnabled(False)
        
        if self._active_model_name == "generic_tree":
            self.update_view()

    def handle_insert(self):
        active_model = self._models[self._active_model_name]
        
        value_str = self._view.value_input.text()
        if not value_str: return
        try: value = int(value_str)
        except ValueError: return
        
        if self._active_model_name == "stack":
            active_model.push(value)

        elif self._active_model_name == "huffman_tree":
            # 哈夫曼树特殊处理：
            # 1. 获取当前输入框已有的内容 (例如 "a:5, b:2")
            try:
                current_text = self._view.huffman_input.text().strip()
            except Exception:
                current_text = ""

            # 2. 构造新项：优先保持用户原始输入 (例如 "a:5" 或 "a: 5")
            # 如果用户只输入了数字 "5"，我们将其转换为 "5:5" 以兼容哈夫曼格式
            if ":" not in value_str:
                new_item = f"{value_str}:{value_str}"
            else:
                new_item = value_str.strip()

            # 3. 追加到字符串中
            if current_text:
                # 检查是否以逗号结尾，处理格式
                if current_text.endswith(','):
                    new_text = f"{current_text} {new_item}"
                else:
                    new_text = f"{current_text}, {new_item}"
            else:
                new_text = new_item

            # 4. 更新界面输入框并立即触发绘制
            try:
                self._view.huffman_input.setText(new_text)
                self.handle_huffman_draw()
            except Exception:
                pass

            # 提示信息
            try:
                self._view.display_info_text(f"已添加哈夫曼节点: {new_item}")
            except Exception:
                pass

        elif self._active_model_name == "b_tree":
            try:
                active_model.insert(value)
                # 更新 B-树 动态讲解文本
                try:
                    t = active_model.t
                    max_k = 2 * t - 1
                    self._current_btree_info = (
                        f"【执行插入】\n"
                        f"已插入元素: {value}\n"
                        f"-----------------------\n"
                        f"检查过程:\n"
                        f"1. 寻找叶子节点位置。\n"
                        f"2. 若节点关键字数 > {max_k - 1} ({max_k}):\n"
                        f"   -> 触发分裂 (Split)\n"
                        f"   -> 中位数上升到父节点"
                    )
                except Exception:
                    self._current_btree_info = None

            except Exception:
                pass
        elif self._active_model_name in ["bst", "avl"]:
            # Debug: 打印即将插入的原始输入与解析后的值（便于追踪意外的合并输入）
            try:
                if self._active_model_name == "avl":
                    print(f"[AVL INSERT] raw='{value_str}' parsed={value}")
            except Exception:
                pass

            # 对AVL模式，先记录插入前的中序快照，用于检测重复插入（不作为新step）
            before_snapshot = None
            if self._active_model_name == "avl":
                try:
                    before_snapshot = active_model.get_inorder_traversal()
                except Exception:
                    before_snapshot = None

            active_model.insert(value)

            # 如果是AVL树，只有当插入改变树结构时才保存历史为新step
            if self._active_model_name == "avl":
                try:
                    after_snapshot = active_model.get_inorder_traversal()
                except Exception:
                    after_snapshot = None

                # 如果插入前后快照相同，则认为是重复元素，**不**记录为新历史步骤
                if before_snapshot is not None and after_snapshot == before_snapshot:
                    try:
                        print(f"[AVL INSERT] duplicate detected, no history append for value={value}")
                    except Exception:
                        pass
                else:
                    # 删除当前步骤之后的所有历史记录（如果有撤销后的新操作）
                    if self._current_avl_step < len(self._avl_history) - 1:
                        self._avl_history = self._avl_history[:self._current_avl_step + 1]
                    # 深拷贝当前状态并添加到历史记录
                    new_root = copy.deepcopy(active_model.root)

                    # 构建展示信息（如果模型记录了 rotation_info，则优先使用）
                    info = {}
                    rot = getattr(active_model, 'rotation_info', None)
                    if rot and rot.get("type"):
                        # 使用 key 而不是节点对象，这样在 deep copy 后也能匹配
                        info = {
                            "highlight_key": rot.get("node").key if rot.get("node") else None,
                            "text": rot.get("message", ""),
                            "rotation_type": rot.get("type"),
                            "balance_info": True
                        }
                    else:
                        info = {"highlight_key": None, "text": f"已插入: {value}", "balance_info": True}

                    # 额外保存一个快照（中序遍历）用于调试与验证历史一致性
                    temp_tree = AVLTree()
                    temp_tree.root = new_root
                    try:
                        snapshot = temp_tree.get_inorder_traversal()
                    except Exception:
                        # 若任何异常发生，仍保证历史记录保存，但快照设为None
                        snapshot = None

                    entry = {"root": new_root, "info": info, "snapshot": snapshot}
                    self._avl_history.append(entry)
                    self._current_avl_step = len(self._avl_history) - 1
                    self._current_avl_info = info
                    # Debug: 输出历史长度与快照，便于追查
                    try:
                        print(f"[AVL HISTORY] appended step={self._current_avl_step} len={len(self._avl_history)} snapshot={snapshot}")
                    except Exception:
                        pass
                    self._update_avl_history_buttons()
        else: # 顺序表和链表
            index_to_insert = active_model.get_length()
            active_model.insert(index_to_insert, value)
        
        self.update_view()
        self._view.value_input.clear()

    def handle_delete(self):
        active_model = self._models[self._active_model_name]
        
        if self._active_model_name == "stack":
            active_model.pop()
        elif self._active_model_name in ["bst", "avl"]:
            value_str = self._view.value_input.text()
            if not value_str: return
            try: value = int(value_str)
            except ValueError: return
            active_model.delete(value)
        else: # 顺序表和链表
            index_to_delete = active_model.get_length() - 1
            if index_to_delete >= 0:
                active_model.delete(index_to_delete)
            else:
                print("列表已空，无法删除")
            
        self.update_view()

    def handle_delete_by_index(self, index):
        """
        AI 专用：根据索引删除元素 (仅适用于 顺序表 和 链表)
        """
        if self._active_model_name not in ["sequential_list", "linked_list"]:
            try:
                self._view.display_info_text("当前结构不支持按索引删除")
            except Exception:
                pass
            return

        # 重置分步演示的状态，防止冲突
        try:
            self.handle_seq_delete_reset()
        except Exception:
            pass

        active_model = self._models[self._active_model_name]
        try:
            length = active_model.get_length()
        except Exception:
            length = None

        if length is None:
            try:
                self._view.display_info_text("删除失败: 无法获取结构长度", QColor("red"))
            except Exception:
                pass
            return

        # 检查索引有效性
        if 0 <= index < length:
            try:
                # 执行删除（顺序表/链表的 delete 接口按索引实现）
                active_model.delete(index)
                try:
                    self._view.display_info_text(f"已删除索引 [{index}] 处的元素")
                except Exception:
                    pass
                self.update_view()
            except Exception as e:
                print(f"删除失败: {e}")
        else:
            try:
                self._view.display_info_text(f"删除失败: 索引 {index} 越界", QColor("red"))
            except Exception:
                pass

    def update_view(self):
        """
        根据当前活动的数据结构，用正确的方式获取数据并调用对应的绘图方法。
        """
        active_model = self._models[self._active_model_name]
        
        if self._active_model_name == "avl":
            # AVL树使用与BST相同的绘制方法，但在节点上显示平衡因子
            # 如果存在当前步骤信息，则传递给视图以便在画面侧边/顶部显示
            info = self._current_avl_info or {"highlight_key": None, "text": "", "balance_info": True}
            self._view.draw_bst(active_model.root, info)
        
        if self._active_model_name in ["sequential_list", "linked_list", "stack"]:
            elements = active_model.get_all_elements()
            if self._active_model_name == "sequential_list":
                # 决定是否有高亮索引（来自顺序表的分步查找/删除）
                highlight_idx = None
                # 插入演示的高亮优先级最高（显示当前遍历/移动/放置位置）
                if getattr(self, '_seq_insert_current_index', None) is not None:
                    highlight_idx = self._seq_insert_current_index
                elif self._seq_search_current_index is not None:
                    highlight_idx = self._seq_search_current_index
                elif self._seq_delete_current_index is not None:
                    highlight_idx = self._seq_delete_current_index
                # 优先使用插入的中间 display_array，其次使用删除的中间 display_array（用于展示移动过程）
                display = self._seq_insert_display_array if self._seq_insert_display_array is not None else self._seq_delete_display_array
                self._view.draw_sequential_list(elements, highlight_index=highlight_idx, display_array=display)
            elif self._active_model_name == "linked_list":
                # 决定是否有高亮索引（来自链表的分步查找/删除/插入）
                highlight_idx = None
                # 插入演示优先显示插入时的高亮位置
                if getattr(self, '_seq_insert_current_index', None) is not None:
                    highlight_idx = self._seq_insert_current_index
                elif self._seq_search_current_index is not None:
                    highlight_idx = self._seq_search_current_index
                elif self._seq_delete_current_index is not None:
                    highlight_idx = self._seq_delete_current_index
                self._view.draw_linked_list(elements, highlight_index=highlight_idx, reconnect_info=self._linked_reconnect_info, insert_info=self._linked_insert_info)
            elif self._active_model_name == "stack":
                # 将可能的短暂栈可视化提示一并传入视图
                viz = getattr(self, '_stack_viz', None)
                self._view.draw_stack(elements, viz=viz)
        elif self._active_model_name == "bst":
            model_root = self._models["bst"].root
            # 优先显示查找演示信息，其次显示删除演示信息
            if getattr(self, '_current_search_info', None):
                info = self._current_search_info
                self._view.draw_bst(model_root, highlight_info=info)
            elif self._current_delete_info:
                info = {"highlight_key": self._highlighted_node_key, "text": self._current_delete_info.get("text", "")}
                self._view.draw_bst(model_root, highlight_info=info)
            else:
                self._view.draw_bst(model_root, highlight_info={"highlight_key": self._highlighted_node_key})
        elif self._active_model_name == "generic_tree":
            model_root = self._models["generic_tree"].root
            self._view.draw_bst(model_root, self._current_build_info)
        elif self._active_model_name == "b_tree":
            model = self._models.get("b_tree")
            if model and model.root:
                try:
                    # 传入当前准备好的 B-树 讲解文本（可能为 None）
                    info = getattr(self, '_current_btree_info', None)
                    self._view.draw_b_tree(model.root, info_text=info)
                except Exception:
                    # Fallback: clear scene if drawing failed
                    try:
                        self._view.scene.clear()
                    except Exception:
                        pass
            else:
                try:
                    self._view.scene.clear()
                except Exception:
                    pass
                # 即使是空树，也显示规则文本（如果存在）
                try:
                    info = getattr(self, '_current_btree_info', None)
                    if info:
                        self._view.draw_right_text_box(info, QColor("#0056b3"))
                except Exception:
                    pass
        elif self._active_model_name == "huffman_tree":
            # 优先绘制分步构建状态
            if self._current_huffman_build_state:
                self._view.draw_huffman_build_step(self._current_huffman_build_state)
            else:
                model = self._models["huffman_tree"]
                if model and model.root:
                    codes = model.generate_codes()
                    self._view.draw_huffman_tree(model.root, codes)
                else:
                    self._view.scene.clear() # 如果没有模型，清空画布
        # 如果视图缓存了要显示的信息文本（例如在开始演示时设置），
        # 在完成绘制后重新将其加入场景，避免被各 draw_* 方法的 scene.clear() 清除。
        try:
            cached = getattr(self._view, '_cached_info_text', None)
            if cached:
                text, color = cached
                try:
                    # 尝试以带颜色的方式显示（视 view 的方法签名而定）
                    self._view.display_info_text(text, color)
                except TypeError:
                    # 备用：如果视图只接受单个参数
                    self._view.display_info_text(text)
        except Exception:
            pass

    def handle_save_structure(self):
        """
        保存当前模型到 JSON 文件
        把内存中复杂的 Python 对象转换成一种简单的、可存储的格式
        """
        model_name = self._active_model_name
        model = self._models.get(model_name)
        if model is None:
            try:
                self._view.display_info_text("当前模型为空，无法保存。")
            except Exception:
                pass
            return

        payload = {"type": model_name}

        try:
            if model_name in ("sequential_list", "linked_list", "stack"):
                elems = model.get_all_elements()
                payload["elements"] = elems

            elif model_name in ("bst", "generic_tree"):
                root = None
                try:
                    root = model.root
                except Exception:
                    root = None
                payload["tree"] = self._serialize_binary_tree(root)

            elif model_name == 'avl':
                root = None
                try:
                    root = model.root
                except Exception:
                    root = None
                payload["tree"] = self._serialize_avl_tree(root)

            elif model_name == 'huffman_tree':
                root = None
                try:
                    root = model.root
                except Exception:
                    root = None
                payload["tree"] = self._serialize_huffman_tree(root)

            else:
                try:
                    self._view.display_info_text(f"不支持保存类型: {model_name}")
                except Exception:
                    pass
                return

            fname, _ = QFileDialog.getSaveFileName(self._view, "保存结构", os.path.expanduser("~"), "JSON Files (*.json);;All Files (*)")
            if not fname:
                return
            if not fname.lower().endswith('.json'):
                fname = fname + '.json'
            with open(fname, 'w', encoding='utf-8') as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
            try:
                self._view.display_info_text(f"已保存到: {fname}")
            except Exception:
                pass
        except Exception as e:
            try:
                self._view.display_info_text(f"保存失败: {e}")
            except Exception:
                pass

    def handle_load_structure(self):
        """从 JSON 文件加载模型并在界面中恢复"""
        try:
            fname, _ = QFileDialog.getOpenFileName(self._view, "打开结构", os.path.expanduser("~"), "JSON Files (*.json);;All Files (*)")
            if not fname:
                return
            with open(fname, 'r', encoding='utf-8') as f:
                payload = json.load(f)
        except Exception as e:
            try:
                self._view.display_info_text(f"打开失败: {e}")
            except Exception:
                pass
            return
        stype = payload.get('type')
        try:
            if stype in ("sequential_list", "linked_list"):
                elems = payload.get('elements', [])
                if stype == 'sequential_list':
                    new_model = SequentialList()
                    for i, v in enumerate(elems):
                        new_model.insert(i, v)
                    self._models['sequential_list'] = new_model
                    self._suppress_structure_side_effects = True
                    try:
                        self._view.radio_sequential_list.setChecked(True)
                    except Exception:
                        pass
                else:
                    new_model = LinkedList()
                    for i, v in enumerate(elems):
                        new_model.insert(i, v)
                    self._models['linked_list'] = new_model
                    self._suppress_structure_side_effects = True
                    try:
                        self._view.radio_linked_list.setChecked(True)
                    except Exception:
                        pass

            elif stype == 'stack':
                elems = payload.get('elements', [])
                new_stack = SequentialStack()
                for v in elems:
                    new_stack.push(v)
                self._models['stack'] = new_stack
                self._suppress_structure_side_effects = True
                try:
                    self._view.radio_stack.setChecked(True)
                except Exception:
                    pass

            elif stype == 'bst':
                tree_data = payload.get('tree')
                root = self._deserialize_binary_tree(tree_data)
                bst = BinarySearchTree()
                bst.root = root
                self._models['bst'] = bst
                self._suppress_structure_side_effects = True
                try:
                    self._view.radio_bst.setChecked(True)
                except Exception:
                    pass

            elif stype == 'avl':
                tree_data = payload.get('tree')
                root = self._deserialize_avl_tree(tree_data)
                avl = AVLTree()
                avl.root = root
                self._models['avl'] = avl
                self._suppress_structure_side_effects = True
                try:
                    self._view.radio_avl.setChecked(True)
                except Exception:
                    pass

            elif stype == 'generic_tree':
                tree_data = payload.get('tree')
                root = self._deserialize_binary_tree(tree_data)
                g = GenericBinaryTree()
                g.root = root
                self._models['generic_tree'] = g
                self._suppress_structure_side_effects = True
                try:
                    self._view.radio_generic_tree.setChecked(True)
                except Exception:
                    pass

            elif stype == 'huffman_tree':
                tree_data = payload.get('tree')
                root = self._deserialize_huffman_tree(tree_data)
                h = HuffmanTree()
                h.root = root
                self._models['huffman_tree'] = h
                self._suppress_structure_side_effects = True
                try:
                    self._view.radio_huffman_tree.setChecked(True)
                except Exception:
                    pass

            else:
                try:
                    self._view.display_info_text("文件不包含可识别的模型类型。")
                except Exception:
                    pass
                return

            # 清除视图中的所有可视元素（如果视图支持此操作）
            try:
                if hasattr(self._view, 'clear_all_visuals'):
                    self._view.clear_all_visuals()
            except Exception:
                pass
            
            # 重置视图状态（如果视图支持此操作）
            try:
                if hasattr(self._view, 'reset_view_for_load'):
                    self._view.reset_view_for_load()
            except Exception:
                pass
            
            try:
                QTimer.singleShot(0, self.update_view)

                if hasattr(self._view, 'center_on_scene_content'):
                    def reset_suppression_and_center():
                        self._suppress_structure_side_effects = False
                        self._view.center_on_scene_content()
                        # 立即在正确的模式下再加载一次，确保显示正确
                        QTimer.singleShot(10, self.update_view)
                    QTimer.singleShot(5, reset_suppression_and_center)
            except Exception:
                try:
                    self.update_view()
                except Exception:
                    pass
                finally:
                    self._suppress_structure_side_effects = False
            try:
                self._view.display_info_text(f"已从 {os.path.basename(fname)} 加载结构。")

                # 定义清理函数：不仅移除视觉元素，还要清除缓存的数据
                def clear_info():
                    # 1. 移除屏幕上的方框（如果存在）
                    try:
                        self._view.clear_cached_right_box()
                    except Exception:
                        pass

                    # 2. 关键修复：清除视图中的文本缓存，避免下一次重绘再次显示旧消息
                    try:
                        if hasattr(self._view, '_cached_info_text'):
                            self._view._cached_info_text = None
                    except Exception:
                        pass

                # 2秒后执行彻底清理
                try:
                    QTimer.singleShot(2000, clear_info)
                except Exception:
                    pass

            except Exception:
                pass
        except Exception as e:
            try:
                self._view.display_info_text(f"恢复结构失败: {e}")
            except Exception:
                pass

    def _serialize_binary_tree(self, node):
        if node is None:
            return None
        return {
            'key': getattr(node, 'key', None),
            'left': self._serialize_binary_tree(getattr(node, 'left', None)),
            'right': self._serialize_binary_tree(getattr(node, 'right', None))
        }

    def _deserialize_binary_tree(self, data):
        if not data:
            return None
        node = TreeNode(data.get('key'))
        node.left = self._deserialize_binary_tree(data.get('left'))
        node.right = self._deserialize_binary_tree(data.get('right'))
        return node

    def _serialize_avl_tree(self, node):
        if node is None:
            return None
        return {
            'key': getattr(node, 'key', None),
            'height': getattr(node, 'height', None),
            'left': self._serialize_avl_tree(getattr(node, 'left', None)),
            'right': self._serialize_avl_tree(getattr(node, 'right', None))
        }

    def _deserialize_avl_tree(self, data):
        if not data:
            return None
        node = AVLNode(data.get('key'))
        try:
            node.height = data.get('height', node.height)
        except Exception:
            pass
        node.left = self._deserialize_avl_tree(data.get('left'))
        node.right = self._deserialize_avl_tree(data.get('right'))
        return node

    def _serialize_huffman_tree(self, node):
        if node is None:
            return None
        return {
            'weight': getattr(node, 'weight', None),
            'char': getattr(node, 'char', None),
            'left': self._serialize_huffman_tree(getattr(node, 'left', None)),
            'right': self._serialize_huffman_tree(getattr(node, 'right', None))
        }

    def _deserialize_huffman_tree(self, data):
        if not data:
            return None
        node = HuffmanNode(weight=data.get('weight'), char=data.get('char'))
        node.left = self._deserialize_huffman_tree(data.get('left'))
        node.right = self._deserialize_huffman_tree(data.get('right'))
        return node