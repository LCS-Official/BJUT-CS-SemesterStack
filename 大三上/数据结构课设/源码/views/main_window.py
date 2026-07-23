# views/main_window.py

import sys
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QPushButton, QLineEdit, QGraphicsView, 
                               QGraphicsScene, QGraphicsRectItem, QGraphicsTextItem,
                               QGraphicsLineItem, QRadioButton, QGroupBox, QGraphicsPolygonItem, QGraphicsEllipseItem,
                               QGraphicsPathItem, QLabel, QSpinBox, QTextEdit)
from PySide6.QtGui import QFont, QBrush, QColor, QPen, QPainterPath, QPixmap
from PySide6.QtCore import Qt, QRectF
from math import sin, cos, radians, atan2, pi
from PySide6.QtCore import QPointF
from PySide6.QtGui import QPolygonF

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("数据结构可视化模拟器")
        self.setGeometry(100, 100, 1200, 800)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # 左侧：控制面板
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        main_layout.addWidget(left_panel, 1)

        # 顶部：演示模式选择
        self.mode_group = QGroupBox("选择演示模式")
        mode_layout = QHBoxLayout()
        self.radio_data_structure = QRadioButton("数据结构演示")
        self.radio_algorithm = QRadioButton("算法演示")
        self.radio_data_structure.setChecked(True)
        mode_layout.addWidget(self.radio_data_structure)
        mode_layout.addWidget(self.radio_algorithm)
        mode_layout.addStretch()
        self.mode_group.setLayout(mode_layout)
        left_layout.addWidget(self.mode_group)

        # 独立的算法模式选择方框
        self.algo_select_group = QGroupBox("选择算法模式")
        algo_sel_layout = QHBoxLayout()
        self.radio_algo_knapsack = QRadioButton("背包问题")
        self.radio_algo_infix = QRadioButton("表达式求值")
        self.radio_algo_paren = QRadioButton("括号匹配")
        self.radio_algo_knapsack.setChecked(True)
        algo_sel_layout.addWidget(self.radio_algo_knapsack)
        algo_sel_layout.addWidget(self.radio_algo_infix)
        algo_sel_layout.addWidget(self.radio_algo_paren)
        algo_sel_layout.addStretch()
        self.algo_select_group.setLayout(algo_sel_layout)
        # 默认隐藏（初始是数据结构模式），由 Controller 控制显示
        self.algo_select_group.setVisible(False)
        left_layout.addWidget(self.algo_select_group)

        
        # 数据结构选择框
        self.structure_group = QGroupBox("选择数据结构")
        structure_layout = QVBoxLayout()
        self.radio_sequential_list = QRadioButton("顺序表")
        self.radio_linked_list = QRadioButton("链表")
        self.radio_stack = QRadioButton("栈")
        self.radio_bst = QRadioButton("二叉搜索树 (动态增删)")
        self.radio_avl = QRadioButton("AVL树 (自平衡二叉树)")
        self.radio_generic_tree = QRadioButton("普通二叉树 (从遍历构建)")
        self.radio_huffman_tree = QRadioButton("哈夫曼树")
        self.radio_b_tree = QRadioButton("B-树 (B-Tree)")
        self.radio_sequential_list.setChecked(True)
        structure_layout.addWidget(self.radio_sequential_list)
        structure_layout.addWidget(self.radio_linked_list)
        structure_layout.addWidget(self.radio_stack)
        structure_layout.addWidget(self.radio_bst)
        structure_layout.addWidget(self.radio_avl)
        structure_layout.addWidget(self.radio_generic_tree)
        structure_layout.addWidget(self.radio_huffman_tree)
        structure_layout.addWidget(self.radio_b_tree)
        self.structure_group.setLayout(structure_layout)
        left_layout.addWidget(self.structure_group)

        # 算法演示区域（包含算法选择与每个算法的控件）
        self.algorithm_group = QGroupBox("算法演示")
        algo_layout = QVBoxLayout()


        # 背包控件放在单独的容器中，便于切换显示/隐藏
        self.knap_widget = QWidget()
        knap_widget_layout = QVBoxLayout(self.knap_widget)
        self.knap_items_input = QLineEdit()
        self.knap_items_input.setPlaceholderText("输入 items: w1, w2, ... 或 w1:v1, w2:v2, ...")
        self.knap_capacity_input = QLineEdit()
        self.knap_capacity_input.setPlaceholderText("目标和 / 背包容量 (整数)")
        knap_widget_layout.addWidget(self.knap_items_input)
        knap_widget_layout.addWidget(self.knap_capacity_input)
        knap_button_layout = QHBoxLayout()
        self.knap_run_button = QPushButton("运行背包问题演示")
        self.knap_next_step_button = QPushButton("下一步")
        self.knap_reset_button = QPushButton("重置")
        self.knap_next_step_button.setEnabled(False)
        knap_button_layout.addWidget(self.knap_run_button)
        knap_button_layout.addWidget(self.knap_next_step_button)
        knap_button_layout.addWidget(self.knap_reset_button)
        knap_widget_layout.addLayout(knap_button_layout)

        # 中缀->后缀控件也放在单独容器
        self.infix_widget = QWidget()
        infix_widget_layout = QVBoxLayout(self.infix_widget)
        self.infix_group_label = QLabel("<b>中缀表达式转后缀 (生成器演示)</b>")
        self.infix_input = QLineEdit()
        self.infix_input.setPlaceholderText("输入中缀表达式, e.g., (a+b)*c - 支持单字符操作数")
        infix_button_layout = QHBoxLayout()
        self.infix_run_button = QPushButton("运行 中缀->后缀")
        self.infix_next_step_button = QPushButton("下一步")
        self.infix_reset_button = QPushButton("重置")
        self.infix_next_step_button.setEnabled(False)
        infix_button_layout.addWidget(self.infix_run_button)
        infix_button_layout.addWidget(self.infix_next_step_button)
        infix_button_layout.addWidget(self.infix_reset_button)
        infix_widget_layout.addWidget(self.infix_group_label)
        infix_widget_layout.addWidget(self.infix_input)
        infix_widget_layout.addLayout(infix_button_layout)

        # 添加分隔线
        from PySide6.QtWidgets import QFrame
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        infix_widget_layout.addWidget(line)

        # 添加后缀求值控件
        self.postfix_eval_label = QLabel("<b>后缀表达式求值 (计算演示)</b>")
        self.postfix_eval_input = QLineEdit()
        self.postfix_eval_input.setPlaceholderText("输入后缀表达式 (空格分隔), e.g., 3 4 + 5 *")
        
        postfix_button_layout = QHBoxLayout()
        self.postfix_eval_run_button = QPushButton("运行 求值")
        self.postfix_eval_next_button = QPushButton("下一步")
        self.postfix_eval_reset_button = QPushButton("重置")
        self.postfix_eval_next_button.setEnabled(False)
        
        postfix_button_layout.addWidget(self.postfix_eval_run_button)
        postfix_button_layout.addWidget(self.postfix_eval_next_button)
        postfix_button_layout.addWidget(self.postfix_eval_reset_button)

        infix_widget_layout.addWidget(self.postfix_eval_label)
        infix_widget_layout.addWidget(self.postfix_eval_input)
        infix_widget_layout.addLayout(postfix_button_layout)

        # 默认只显示背包控件，隐藏表达式转换控件
        self.infix_widget.setVisible(False)
        self.paren_match_widget = QWidget()
        paren_layout = QVBoxLayout(self.paren_match_widget)
        
        self.paren_input = QLineEdit()
        self.paren_input.setPlaceholderText("输入待检测字符串, e.g., { [ ( ) ] }")
        self.paren_input.setText("{[()]}")
        
        paren_btn_layout = QHBoxLayout()
        self.paren_run_button = QPushButton("开始检测")
        self.paren_next_button = QPushButton("下一步")
        self.paren_reset_button = QPushButton("重置")
        self.paren_next_button.setEnabled(False)
        
        paren_btn_layout.addWidget(self.paren_run_button)
        paren_btn_layout.addWidget(self.paren_next_button)
        paren_btn_layout.addWidget(self.paren_reset_button)
        
        paren_layout.addWidget(QLabel("<b>括号匹配可视化</b>"))
        paren_layout.addWidget(self.paren_input)
        paren_layout.addLayout(paren_btn_layout)
        
        # 默认隐藏
        self.paren_match_widget.setVisible(False)
        
        # 添加到算法布局中
        algo_layout.addWidget(self.knap_widget)
        algo_layout.addWidget(self.infix_widget)
        algo_layout.addWidget(self.paren_match_widget)

        self.algorithm_group.setLayout(algo_layout)
        # 默认隐藏算法演示组
        self.algorithm_group.setVisible(False)
        left_layout.addWidget(self.algorithm_group)

        # 通用输入框
        self.value_input = QLineEdit()
        self.value_input.setPlaceholderText("输入数值...")
        left_layout.addWidget(self.value_input)
        
        # 动态操作面板
        self.dynamic_ops_group = QGroupBox("动态操作")
        
        # 主布局改回垂直，为了让“分步演示”在按钮下方
        dynamic_ops_main_layout = QVBoxLayout() 
        
        # 创建一个内部水平布局，专门放“添加”和“移除”按钮
        buttons_row_layout = QHBoxLayout()
        self.insert_button = QPushButton("添加")
        self.delete_button = QPushButton("移除")
        buttons_row_layout.addWidget(self.insert_button)
        buttons_row_layout.addWidget(self.delete_button)
        
        # 将按钮行添加到主垂直布局
        dynamic_ops_main_layout.addLayout(buttons_row_layout)

        # 顺序表分步演示（查询 / 删除）
        self.seq_step_group = QGroupBox("顺序表 分步演示")
        seq_step_layout = QVBoxLayout() # 分步演示内部保持垂直布局

        seq_search_row = QHBoxLayout()
        self.seq_search_start = QPushButton("查询")
        self.seq_search_next = QPushButton("下一步")
        self.seq_search_next.setEnabled(False)
        self.seq_search_reset = QPushButton("重置 查询")
        self.seq_search_reset.setEnabled(False)
        seq_search_row.addWidget(self.seq_search_start)
        seq_search_row.addWidget(self.seq_search_next)
        seq_search_row.addWidget(self.seq_search_reset)
        seq_step_layout.addLayout(seq_search_row)

        seq_delete_row = QHBoxLayout()
        self.seq_delete_start = QPushButton("删除")
        self.seq_delete_next = QPushButton("下一步")
        self.seq_delete_next.setEnabled(False)
        self.seq_delete_reset = QPushButton("重置 删除")
        self.seq_delete_reset.setEnabled(False)
        seq_delete_row.addWidget(self.seq_delete_start)
        seq_delete_row.addWidget(self.seq_delete_next)
        seq_delete_row.addWidget(self.seq_delete_reset)
        seq_step_layout.addLayout(seq_delete_row)

        # 插入操作行
        seq_insert_row = QHBoxLayout()
        self.seq_insert_index_input = QLineEdit()
        self.seq_insert_index_input.setPlaceholderText("索引")
        self.seq_insert_value_input = QLineEdit()
        self.seq_insert_value_input.setPlaceholderText("插入值")
        self.seq_insert_button = QPushButton("插入/下一步")
        self.seq_insert_reset = QPushButton("重置")
        self.seq_insert_reset.setEnabled(False)
        seq_insert_row.addWidget(self.seq_insert_index_input)
        seq_insert_row.addWidget(self.seq_insert_value_input)
        seq_insert_row.addWidget(self.seq_insert_button)
        seq_insert_row.addWidget(self.seq_insert_reset)
        seq_step_layout.addLayout(seq_insert_row)

        self.seq_step_group.setLayout(seq_step_layout)
        # 默认隐藏，只有在顺序表模式下显示
        self.seq_step_group.setVisible(False)
        
        # 将分步演示组添加到主垂直布局（位于按钮行下方）
        dynamic_ops_main_layout.addWidget(self.seq_step_group)
        
        # 应用主布局
        self.dynamic_ops_group.setLayout(dynamic_ops_main_layout)
        left_layout.addWidget(self.dynamic_ops_group)

        # 分步删除演示按钮
        self.delete_step_group = QGroupBox("分步删除演示 (仅BST)")
        delete_step_layout = QVBoxLayout()
        
        self.start_delete_button = QPushButton("开始删除演示")
        
        delete_buttons_layout = QHBoxLayout()
        self.prev_delete_step_button = QPushButton("上一步")
        self.next_delete_step_button = QPushButton("下一步")
        
        delete_buttons_layout.addWidget(self.prev_delete_step_button)
        delete_buttons_layout.addWidget(self.next_delete_step_button)

        self.reset_delete_button = QPushButton("重置")
        
        self.prev_delete_step_button.setEnabled(False)
        self.next_delete_step_button.setEnabled(False)
        self.reset_delete_button.setEnabled(False)

        delete_step_layout.addWidget(self.start_delete_button)
        delete_step_layout.addLayout(delete_buttons_layout)
        delete_step_layout.addWidget(self.reset_delete_button)
        
        self.delete_step_group.setLayout(delete_step_layout)

        # 保存/打开 按钮（用于保存/加载结构状态）
        self.file_ops_group = QGroupBox("文件")
        file_ops_layout = QHBoxLayout()
        self.save_structure_button = QPushButton("保存结构")
        self.load_structure_button = QPushButton("打开结构")
        file_ops_layout.addWidget(self.save_structure_button)
        file_ops_layout.addWidget(self.load_structure_button)
        self.file_ops_group.setLayout(file_ops_layout)
        left_layout.addWidget(self.file_ops_group)

        left_layout.addWidget(self.delete_step_group)

        # 查找操作面板
        self.search_ops_group = QGroupBox("查找操作 (仅BST)")
        search_ops_layout = QHBoxLayout()  # 使用水平布局
        self.search_button = QPushButton("开始查找")
        self.next_step_button = QPushButton("下一步")
        self.reset_button = QPushButton("重置状态")
        self.next_step_button.setEnabled(False) 
        self.reset_button.setEnabled(False)
        search_ops_layout.addWidget(self.search_button)
        search_ops_layout.addWidget(self.next_step_button)
        search_ops_layout.addWidget(self.reset_button)
        self.search_ops_group.setLayout(search_ops_layout)
        left_layout.addWidget(self.search_ops_group)

        # 栈操作面板 (仅Stack)
        self.stack_ops_group = QGroupBox("栈 操作")
        stack_ops_layout = QVBoxLayout()
        # 使用 value_input 作为通用输入框，Push 会读取该值
        self.stack_push_button = QPushButton("入栈 (Push)")
        self.stack_pop_button = QPushButton("出栈 (Pop)")
        self.stack_top_button = QPushButton("查看栈顶 (Top)")
        stack_ops_layout.addWidget(self.stack_push_button)
        stack_ops_layout.addWidget(self.stack_pop_button)
        stack_ops_layout.addWidget(self.stack_top_button)
        self.stack_ops_group.setLayout(stack_ops_layout)
        self.stack_ops_group.setVisible(False)
        left_layout.addWidget(self.stack_ops_group)

        # BST 构建面板
        self.bst_build_group = QGroupBox("从序列构建BST")
        bst_build_layout = QVBoxLayout()
        self.bst_build_input = QLineEdit()
        self.bst_build_input.setPlaceholderText("e.g., 50,30,70,20,40,60,80")
        self.bst_build_button = QPushButton("构建BST")
        bst_build_layout.addWidget(QLabel("<b>输入节点值 (用逗号分隔):</b>"))
        bst_build_layout.addWidget(self.bst_build_input)
        # 按钮行：构建 + 随机生成序列
        bst_button_row = QHBoxLayout()
        self.bst_random_button = QPushButton("随机生成序列")
        bst_button_row.addWidget(self.bst_build_button)
        bst_button_row.addWidget(self.bst_random_button)
        bst_build_layout.addLayout(bst_button_row)
        # 在最下方增加一个重置树按钮，用于清空当前BST
        self.bst_reset_tree_button = QPushButton("重置树")
        bst_build_layout.addWidget(self.bst_reset_tree_button)
        self.bst_build_group.setLayout(bst_build_layout)
        left_layout.addWidget(self.bst_build_group)

        # AVL树历史操作面板
        self.avl_history_group = QGroupBox("历史操作 (仅AVL)")
        avl_history_layout = QVBoxLayout()
        self.avl_prev_button = QPushButton("上一步 (撤销)")
        self.avl_next_button = QPushButton("下一步 (重做)")
        self.avl_history_reset_button = QPushButton("重置历史")
        avl_history_layout.addWidget(self.avl_prev_button)
        avl_history_layout.addWidget(self.avl_next_button)
        avl_history_layout.addWidget(self.avl_history_reset_button)
        self.avl_history_group.setLayout(avl_history_layout)
        left_layout.addWidget(self.avl_history_group)
        
        # 初始隐藏特定于模式的UI
        self.delete_step_group.setVisible(False)
        self.search_ops_group.setVisible(False)
        self.bst_build_group.setVisible(False)
        self.avl_history_group.setVisible(False)

        # 哈夫曼树构建面板
        self.huffman_group = QGroupBox("哈夫曼树构建")
        huffman_layout = QVBoxLayout()
        self.huffman_input = QLineEdit()
        self.huffman_input.setPlaceholderText("e.g., a:5, b:9, c:12, d:13, e:16, f:45")
        
        # 使用两行按钮布局，减少单行过长的问题
        huffman_button_layout_v = QVBoxLayout()
        huffman_button_row1 = QHBoxLayout()
        huffman_button_row2 = QHBoxLayout()

        # 随机生成按钮：为哈夫曼输入框生成随机字母权重对
        self.huffman_random_button = QPushButton("随机生成")
        self.huffman_draw_button = QPushButton("立刻绘制")
        self.huffman_start_button = QPushButton("开始演示")
        self.huffman_prev_step_button = QPushButton("上一步")
        self.huffman_next_step_button = QPushButton("下一步")
        self.huffman_reset_button = QPushButton("重置")

        # 第一行：随机生成、开始演示、重置
        huffman_button_row1.addWidget(self.huffman_random_button)
        huffman_button_row1.addWidget(self.huffman_start_button)
        huffman_button_row1.addWidget(self.huffman_reset_button)

        # 第二行：立刻绘制、上一步、下一步
        huffman_button_row2.addWidget(self.huffman_draw_button)
        huffman_button_row2.addWidget(self.huffman_prev_step_button)
        huffman_button_row2.addWidget(self.huffman_next_step_button)

        # 初始按钮状态
        self.huffman_prev_step_button.setEnabled(False)
        self.huffman_next_step_button.setEnabled(False)
        self.huffman_reset_button.setEnabled(False)

        huffman_button_layout_v.addLayout(huffman_button_row1)
        huffman_button_layout_v.addLayout(huffman_button_row2)

        huffman_layout.addWidget(QLabel("<b>输入字符及其权重 (用逗号分隔):</b>"))
        huffman_layout.addWidget(self.huffman_input)
        huffman_layout.addLayout(huffman_button_layout_v)
        self.huffman_group.setLayout(huffman_layout)
        left_layout.addWidget(self.huffman_group)
        self.huffman_group.setVisible(False)

        # B-树 设置面板
        self.b_tree_group = QGroupBox("B-树 参数设置")
        btree_layout = QVBoxLayout()
        
        # 阶数输入行
        degree_row = QHBoxLayout()
        degree_row.addWidget(QLabel("最小度数 t (t≥2):"))
        self.btree_degree_spin = QSpinBox()
        self.btree_degree_spin.setRange(2, 10) # 设置范围，太大会很难画
        self.btree_degree_spin.setValue(3)     # 默认值 t=3
        degree_row.addWidget(self.btree_degree_spin)
        btree_layout.addLayout(degree_row)
        
        # 说明标签
        info_label = QLabel("注: 节点最大关键字数 = 2t - 1")
        info_label.setStyleSheet("color: gray; font-size: 10px;")
        btree_layout.addWidget(info_label)

        # 确认/重置按钮
        self.btree_set_button = QPushButton("重置并应用新阶数")
        btree_layout.addWidget(self.btree_set_button)
        
        self.b_tree_group.setLayout(btree_layout)
        left_layout.addWidget(self.b_tree_group)
        self.b_tree_group.setVisible(False) # 默认隐藏

        # 构建面板
        self.build_tree_group = QGroupBox("从遍历序列构建")
        build_tree_layout = QVBoxLayout()
        # 输入框创建
        build_tree_layout.addWidget(QLabel("<b>方法一: 前序 + 中序 (DFT)</b>"))
        self.preorder_input = QLineEdit()
        self.preorder_input.setPlaceholderText("前序, e.g., 1,2,4,5,3,6")
        self.inorder_input_pre = QLineEdit() 
        self.inorder_input_pre.setPlaceholderText("中序, e.g., 4,2,5,1,6,3")
        build_tree_layout.addWidget(self.preorder_input)
        build_tree_layout.addWidget(self.inorder_input_pre)
        # 随机生成前序+中序序列按钮
        pre_in_btn_row = QHBoxLayout()
        self.pre_in_random_button = QPushButton("随机生成序列")
        pre_in_btn_row.addWidget(self.pre_in_random_button)
        build_tree_layout.addLayout(pre_in_btn_row)
        build_tree_layout.addWidget(QLabel("<b>方法二: 后序 + 中序 (DFT)</b>"))
        self.postorder_input = QLineEdit()
        self.postorder_input.setPlaceholderText("后序, e.g., 4,5,2,6,3,1")
        self.inorder_input_post = QLineEdit()
        self.inorder_input_post.setPlaceholderText("中序, e.g., 4,2,5,1,6,3")
        build_tree_layout.addWidget(self.postorder_input)
        build_tree_layout.addWidget(self.inorder_input_post)
        # 随机生成后序+中序序列按钮
        post_in_btn_row = QHBoxLayout()
        self.post_in_random_button = QPushButton("随机生成序列")
        post_in_btn_row.addWidget(self.post_in_random_button)
        build_tree_layout.addLayout(post_in_btn_row)
        build_tree_layout.addWidget(QLabel("<b>方法三: 层序 (BFT, 空节点用'null')</b>"))
        self.levelorder_input = QLineEdit()
        self.levelorder_input.setPlaceholderText("e.g., 1,2,3,null,4,null,5")
        build_tree_layout.addWidget(self.levelorder_input)

        # 层序随机生成按钮
        level_btn_row = QHBoxLayout()
        self.level_random_button = QPushButton("随机生成序列")
        level_btn_row.addWidget(self.level_random_button)
        build_tree_layout.addLayout(level_btn_row)

        # 新的按钮组
        build_button_layout = QHBoxLayout()
        self.start_build_button = QPushButton("开始演示")
        self.next_build_step_button = QPushButton("下一步")
        self.reset_build_button = QPushButton("重置")
        self.next_build_step_button.setEnabled(False)
        self.reset_build_button.setEnabled(False)
        build_button_layout.addWidget(self.start_build_button)
        build_button_layout.addWidget(self.next_build_step_button)
        build_button_layout.addWidget(self.reset_build_button)
        
        build_tree_layout.addLayout(build_button_layout) # 添加按钮组
        self.build_tree_group.setLayout(build_tree_layout)
        left_layout.addWidget(self.build_tree_group)
        self.build_tree_group.setVisible(False)

        left_layout.addStretch()

        # 右侧绘图区域
        self.canvas = QGraphicsView()
        self.scene = QGraphicsScene()
        self.canvas.setScene(self.scene)
        try:
            self.canvas.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
            self.canvas.setCacheMode(QGraphicsView.CacheNone)

            try:
                self.canvas.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
                self.canvas.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            except Exception:
                pass
        except Exception:
            pass
        main_layout.addWidget(self.canvas, 3)

        # 右侧面板：AI 智能助手
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        # 将右侧面板改为固定宽度彻底防止它忽大忽小
        right_panel.setFixedWidth(280)
        right_panel.setMaximumHeight(600)

        self.ai_group = QGroupBox("AI 智能助手")
        ai_layout = QVBoxLayout()

        # 聊天记录显示
        self.ai_chat_display = QTextEdit()
        self.ai_chat_display.setReadOnly(True)
        # 固定聊天显示区高度，输入框位于其下方
        self.ai_chat_display.setFixedHeight(500)
        self.ai_chat_display.setPlaceholderText("我是你的数据结构助手。你可以说：\n'帮我建一个由 10, 20, 5 组成的 BST'\n'把 20 删掉'\n'切换到 AVL 树'")
        
        # 输入区域
        ai_input_layout = QHBoxLayout()
        self.ai_input = QLineEdit()
        self.ai_input.setPlaceholderText("输入指令...")
        self.ai_send_button = QPushButton("发送")

        ai_input_layout.addWidget(self.ai_input)
        ai_input_layout.addWidget(self.ai_send_button)

        ai_layout.addWidget(self.ai_chat_display)
        ai_layout.addLayout(ai_input_layout)

        self.ai_group.setLayout(ai_layout)
        
        # 将 AI Group 加入右侧布局
        right_layout.addWidget(self.ai_group)

        # 用于在右侧面板显示 B-树阶数说明的图片控件（默认隐藏）
        self.image_label = QLabel()
        self.image_label.setVisible(False)
        self.image_label.setScaledContents(True)
        # 限制图片最大宽度以避免撑破右侧面板
        self.image_label.setMaximumWidth(260)
        right_layout.addWidget(self.image_label)
        
        # 将伸缩因子 (stretch) 设为 0
        # 这样右侧面板就不会参与剩余空间的分配，而是保持固定宽度
        main_layout.addWidget(right_panel, 0)


    def draw_sequential_list(self, elements: list, highlight_index=None, display_array=None):
        """
        根据给定的列表数据，在画布上绘制顺序表
        """
        try:
            self.clear_cached_right_box()
        except Exception:
            pass
        self.scene.clear() # 每次重绘前清空画布

        x_offset = 10
        y_offset = 80
        box_width = 60
        box_height = 60
        spacing = 10
        # 如果提供了 display_array，则使用它来渲染（可用于显示中间移动状态），否则使用模型元素
        arr = display_array if display_array is not None else elements

        for i, value in enumerate(arr):
            # 计算每个方块的位置
            x = x_offset + i * (box_width + spacing)

            # 绘制方块
            rect_item = QGraphicsRectItem(x, y_offset, box_width, box_height)

            # 如果当前索引为高亮索引，则使用黄色背景并红色边框
            if highlight_index is not None and i == highlight_index:
                rect_item.setBrush(QBrush(QColor("#fff3b0")))
                rect_item.setPen(QPen(QColor("red"), 3))
            else:
                if value is None:
                    # 空位显示为深色空框
                    rect_item.setBrush(QBrush(QColor("#2f2f2f")))
                else:
                    rect_item.setBrush(QBrush(QColor("#a2d2ff"))) # 设置填充颜色
            self.scene.addItem(rect_item)

            # 绘制方块内的文本（如果为 None 则不显示文本）
            if value is not None:
                text_item = QGraphicsTextItem(str(value))
                text_item.setFont(QFont("Arial", 14))
                # 节点文本使用深紫色
                text_item.setDefaultTextColor(QColor("#4B0082"))
                # 将文本居中
                text_x = x + (box_width - text_item.boundingRect().width()) / 2
                text_y = y_offset + (box_height - text_item.boundingRect().height()) / 2
                text_item.setPos(text_x, text_y)
                self.scene.addItem(text_item)

            # 绘制索引标签在方框下方
            idx_text = QGraphicsTextItem(str(i))
            idx_text.setFont(QFont("Arial", 10))
            idx_text.setDefaultTextColor(QColor("lightgray"))
            idx_x = x + (box_width - idx_text.boundingRect().width()) / 2
            idx_y = y_offset + box_height + 4
            idx_text.setPos(idx_x, idx_y)
            self.scene.addItem(idx_text)
        # 自动缩放视图以适应内容
        try:
            self._auto_scale_view(padding=60, min_scale=0.1)
        except Exception:
            pass
    
    def draw_knapsack_backtracking_demo(self, items, weights, current_stack_indices, 
                                        discarded_indices, remaining_capacity, capacity, highlighted_action=None):
        """
        绘制背包问题的完整演示：左边物品列表，中间栈区，右边丢弃区与状态信息
        """
        self.clear_cached_right_box()
        self.scene.clear()
        
        # 分区布局 - 增加各区域之间的间隔
        items_x = 20
        items_y = 80
        stack_x = 280
        stack_y = 80
        discard_x = 550
        discard_y = 80
        info_x = 800
        info_y = 80
        
        box_w, box_h = 50, 50
        spacing = 15
        # 每行显示的物品数量（可调整）
        items_per_row = 3
        
        # 绘制物品列表区
        list_label = QGraphicsTextItem("待放入物品")
        list_label.setFont(QFont("Arial", 10, QFont.Bold))
        list_label.setPos(items_x, items_y - 30)
        self.scene.addItem(list_label)
        
        for i, w in enumerate(weights):
            x = items_x + (i % items_per_row) * (box_w + spacing)
            y = items_y + (i // items_per_row) * (box_h + spacing)
            
            # 根据是否在栈中选择颜色
            is_in_stack = i in current_stack_indices
            color = QColor(144, 238, 144) if is_in_stack else QColor(200, 200, 200)  # 绿/灰
            
            # 高亮正在 push 或 pop 的项
            if highlighted_action and highlighted_action.get("index") == i:
                if highlighted_action.get("type") == "入栈":
                    color = QColor(255, 255, 100)  # 黄色 = 正在进栈
                elif highlighted_action.get("type") == "出栈":
                    color = QColor(255, 150, 150)  # 红色 = 正在出栈
            
            rect = QGraphicsRectItem(x, y, box_w, box_h)
            rect.setBrush(QBrush(color))
            rect.setPen(QPen(QColor(0, 0, 0), 2))
            self.scene.addItem(rect)
            
            text = QGraphicsTextItem(str(w))
            text.setFont(QFont("Arial", 9))
            text.setDefaultTextColor(QColor("#36025c"))  # 深紫色
            text.setPos(x + 5, y + 15)
            self.scene.addItem(text)
        
        # 绘制栈区
        stack_label = QGraphicsTextItem("栈演示")
        stack_label.setFont(QFont("Arial", 10, QFont.Bold))
        stack_label.setPos(stack_x, stack_y - 30)
        self.scene.addItem(stack_label)
        
        for i, idx in enumerate(current_stack_indices):
            x = stack_x
            y = stack_y + i * (box_h + spacing)
            w = weights[idx]
            
            rect = QGraphicsRectItem(x, y, box_w, box_h)
            rect.setBrush(QBrush(QColor("darkblue")))  # 深蓝 = 已入栈
            rect.setPen(QPen(QColor(0, 100, 0), 2))
            self.scene.addItem(rect)
            
            text = QGraphicsTextItem(f"{idx}:{w}")
            text.setFont(QFont("Arial", 8))
            text.setPos(x + 3, y + 15)
            self.scene.addItem(text)
        
        # 绘制丢弃区
        discard_label = QGraphicsTextItem("被丢弃物品")
        discard_label.setFont(QFont("Arial", 10, QFont.Bold))
        discard_label.setPos(discard_x, discard_y - 30)
        self.scene.addItem(discard_label)
        
        # 绘制被丢弃的物品（参数中传入的 discarded_indices）
        discard_y_offset = discard_y
        for idx, item_idx in enumerate(discarded_indices):
            x = discard_x
            y = discard_y_offset
            w = weights[item_idx]
            
            rect = QGraphicsRectItem(x, y, box_w, box_h)
            rect.setBrush(QBrush(QColor(220, 100, 100)))  # 浅红 = 被丢弃
            rect.setPen(QPen(QColor(139, 0, 0), 2))  # 深红边框
            self.scene.addItem(rect)
            
            text = QGraphicsTextItem(f"{item_idx}:{w}")
            text.setFont(QFont("Arial", 8))
            text.setDefaultTextColor(QColor("#36025c"))  # 深紫色
            text.setPos(x + 3, y + 15)
            self.scene.addItem(text)
            
            discard_y_offset += box_h + spacing
        
        # 绘制状态信息
        info_y_offset = info_y
        info_lines = [
            f"剩余容量: {remaining_capacity}/{capacity}",
            f"当前栈容量: {len(current_stack_indices)}",
            f"放入的物品index: {list(current_stack_indices)}"
        ]
        for line in info_lines:
            text = QGraphicsTextItem(line)
            text.setFont(QFont("Arial", 9))
            text.setPos(info_x, info_y_offset)
            self.scene.addItem(text)
            info_y_offset += 25
        
        # 绘制进度条
        progress_w = 200
        progress_h = 20
        progress_x = info_x
        progress_y = info_y_offset + 20
        
        # 背景
        bg = QGraphicsRectItem(progress_x, progress_y, progress_w, progress_h)
        bg.setBrush(QBrush(QColor(220, 220, 220)))
        bg.setPen(QPen(QColor(100, 100, 100), 1))
        self.scene.addItem(bg)
        
        # 进度（已用容量占比）
        used = capacity - remaining_capacity
        progress_ratio = used / capacity if capacity > 0 else 0
        progress_w_actual = progress_w * progress_ratio
        
        fg = QGraphicsRectItem(progress_x, progress_y, progress_w_actual, progress_h)
        fg.setBrush(QBrush(QColor(100, 200, 100)))
        self.scene.addItem(fg)
        
        # 自动缩放
        try:
            self._auto_scale_view(padding=40, min_scale=0.15)
        except Exception:
            pass
    
    def draw_infix_postfix_demo(self, stack_elements, postfix_str, current_token, action_text):
        """
        专门用于中缀转后缀的演示绘制：
        顶部：当前扫描的字符 (Token)
        左侧：运算符栈 (Stack)
        右侧：结果后缀表达式 (Postfix Output)
        底部：操作说明
        """
        # 清除旧的视觉元素（包括右上角的信息框）
        self.clear_all_visuals()
        self.scene.clear()

        # 布局参数 (逻辑坐标) 
        cx, cy = 400, 300  # 假设场景中心
        
        # 绘制顶部：当前扫描字符
        token_y = cy - 200
        token_box_size = 60
        
        token_label = QGraphicsTextItem("当前扫描字符")
        token_label.setFont(QFont("Arial", 12, QFont.Bold))
        token_label.setDefaultTextColor(QColor("gray"))
        token_label.setPos(cx - token_label.boundingRect().width()/2, token_y - 30)
        self.scene.addItem(token_label)

        # 字符框
        rect = QGraphicsRectItem(cx - token_box_size/2, token_y, token_box_size, token_box_size)
        if current_token and current_token != "END" and current_token != "DONE":
            rect.setBrush(QBrush(QColor("#fff3b0"))) # 黄色高亮
            t_str = str(current_token)
        else:
            rect.setBrush(QBrush(QColor("#f0f0f0"))) # 灰色占位
            t_str = ""
            
        rect.setPen(QPen(QColor("black"), 2))
        self.scene.addItem(rect)
        
        if t_str:
            t_item = QGraphicsTextItem(t_str)
            t_item.setFont(QFont("Arial", 18, QFont.Bold))
            t_item.setDefaultTextColor(QColor("black"))
            tx = cx - t_item.boundingRect().width()/2
            ty = token_y + (token_box_size - t_item.boundingRect().height())/2
            t_item.setPos(tx, ty)
            self.scene.addItem(t_item)

        # 绘制左侧：运算符栈
        stack_x = cx - 180
        stack_base_y = cy + 100
        box_w, box_h = 60, 40
        
        stack_title = QGraphicsTextItem("运算符栈")
        stack_title.setFont(QFont("Arial", 12, QFont.Bold))
        stack_title.setDefaultTextColor(QColor("#007acc")) # 蓝色标题
        stack_title.setPos(stack_x - stack_title.boundingRect().width()/2, stack_base_y + 10)
        self.scene.addItem(stack_title)
        
        # 栈底基准线
        base_line = QGraphicsLineItem(stack_x - 50, stack_base_y, stack_x + 50, stack_base_y)
        base_line.setPen(QPen(QColor("black"), 3))
        self.scene.addItem(base_line)

        # 绘制栈元素（从下往上堆叠）
        for i, val in enumerate(stack_elements):
            rect = QGraphicsRectItem(stack_x - box_w/2, stack_base_y - (i+1)*box_h, box_w, box_h)
            rect.setBrush(QBrush(QColor("#a2d2ff"))) # 浅蓝
            rect.setPen(QPen(QColor("black"), 1))
            self.scene.addItem(rect)
            
            txt = QGraphicsTextItem(str(val))
            txt.setFont(QFont("Arial", 14))
            txt.setPos(stack_x - txt.boundingRect().width()/2, stack_base_y - (i+1)*box_h + (box_h - txt.boundingRect().height())/2)
            self.scene.addItem(txt)

        # 绘制右侧：后缀表达式序列
        postfix_x_start = cx + 20
        postfix_y = cy
        
        postfix_title = QGraphicsTextItem("后缀表达式 (结果)")
        postfix_title.setFont(QFont("Arial", 12, QFont.Bold))
        postfix_title.setDefaultTextColor(QColor("#2e8b57")) # 深绿标题
        postfix_title.setPos(postfix_x_start, postfix_y - 40)
        self.scene.addItem(postfix_title)

        # 绘制序列方块 (水平排列)
        pf_box_w, pf_box_h = 40, 40
        gap = 5
        
        for i, char in enumerate(postfix_str):
            px = postfix_x_start + i * (pf_box_w + gap)
            py = postfix_y
            
            rect = QGraphicsRectItem(px, py, pf_box_w, pf_box_h)
            rect.setBrush(QBrush(QColor("#90ee90"))) # 浅绿
            rect.setPen(QPen(QColor("black"), 1))
            self.scene.addItem(rect)
            
            txt = QGraphicsTextItem(str(char))
            txt.setFont(QFont("Arial", 12))
            txt.setPos(px + (pf_box_w - txt.boundingRect().width())/2, py + (pf_box_h - txt.boundingRect().height())/2)
            self.scene.addItem(txt)

        # 绘制下方：操作说明
        info_y = cy + 160
        if action_text:
            # 背景框
            info_bg = QGraphicsRectItem(cx - 300, info_y, 600, 50)
            info_bg.setBrush(QBrush(QColor("#f9f9f9")))
            info_bg.setPen(QPen(QColor("#cccccc"), 1))
            self.scene.addItem(info_bg)
            
            info_item = QGraphicsTextItem(action_text)
            info_item.setFont(QFont("Arial", 14))
            info_item.setDefaultTextColor(QColor("#333333"))
            info_item.setPos(cx - info_item.boundingRect().width()/2, info_y + (50 - info_item.boundingRect().height())/2)
            self.scene.addItem(info_item)

        # 自动缩放以适应内容
        try:
            self._auto_scale_view(padding=50)
        except Exception:
            pass
    
    def draw_postfix_evaluation_demo(self, stack_elements, current_token, action_text, calc_info=None):
        """
        绘制后缀表达式求值过程
        calc_info: dict, optional, 包含 {v1, v2, op} 用于显示计算过程动画
        """
        self.clear_all_visuals()
        self.scene.clear()

        cx, cy = 400, 300
        
        # 1. 顶部：当前扫描 Token
        token_y = cy - 220
        token_box_size = 70
        
        token_label = QGraphicsTextItem("当前 Token")
        token_label.setFont(QFont("Arial", 12, QFont.Bold))
        token_label.setDefaultTextColor(QColor("gray"))
        token_label.setPos(cx - token_label.boundingRect().width()/2, token_y - 30)
        self.scene.addItem(token_label)

        rect = QGraphicsRectItem(cx - token_box_size/2, token_y, token_box_size, token_box_size)
        rect.setBrush(QBrush(QColor("#ffdfba"))) # 浅橙色
        rect.setPen(QPen(QColor("black"), 2))
        self.scene.addItem(rect)
        
        if current_token and current_token not in ("START", "DONE"):
            t_item = QGraphicsTextItem(str(current_token))
            t_item.setFont(QFont("Arial", 18, QFont.Bold))
            tx = cx - t_item.boundingRect().width()/2
            ty = token_y + (token_box_size - t_item.boundingRect().height())/2
            t_item.setPos(tx, ty)
            self.scene.addItem(t_item)

        # 2. 中间：计算栈
        stack_x = cx
        stack_base_y = cy + 150
        box_w, box_h = 80, 50
        
        stack_title = QGraphicsTextItem("计算结果栈")
        stack_title.setFont(QFont("Arial", 12, QFont.Bold))
        stack_title.setDefaultTextColor(QColor("#007acc"))
        stack_title.setPos(stack_x - stack_title.boundingRect().width()/2, stack_base_y + 10)
        self.scene.addItem(stack_title)
        
        base_line = QGraphicsLineItem(stack_x - 60, stack_base_y, stack_x + 60, stack_base_y)
        base_line.setPen(QPen(QColor("black"), 3))
        self.scene.addItem(base_line)

        for i, val in enumerate(stack_elements):
            rect = QGraphicsRectItem(stack_x - box_w/2, stack_base_y - (i+1)*box_h, box_w, box_h)
            rect.setBrush(QBrush(QColor("#bae1ff"))) # 浅蓝色
            rect.setPen(QPen(QColor("black"), 1))
            self.scene.addItem(rect)
            
            txt = QGraphicsTextItem(str(val))
            txt.setFont(QFont("Arial", 14))
            txt.setPos(stack_x - txt.boundingRect().width()/2, stack_base_y - (i+1)*box_h + (box_h - txt.boundingRect().height())/2)
            self.scene.addItem(txt)

        # 3. 如果正在进行计算（Pop两个数），在左右两侧显示被弹出的数
        if calc_info:
            v1, v2, op = calc_info['v1'], calc_info['v2'], calc_info['op']
            
            # 左操作数
            l_rect = QGraphicsRectItem(cx - 200, cy, 60, 60)
            l_rect.setBrush(QBrush(QColor("#ffb3ba")))
            self.scene.addItem(l_rect)
            l_txt = QGraphicsTextItem(str(v1))
            l_txt.setFont(QFont("Arial", 14))
            l_txt.setPos(cx - 200 + (60-l_txt.boundingRect().width())/2, cy + (60-l_txt.boundingRect().height())/2)
            self.scene.addItem(l_txt)
            l_label = QGraphicsTextItem(f"左: {v1}")
            l_label.setPos(cx-200, cy-25)
            self.scene.addItem(l_label)

            # 右操作数
            r_rect = QGraphicsRectItem(cx + 140, cy, 60, 60)
            r_rect.setBrush(QBrush(QColor("#ffb3ba")))
            self.scene.addItem(r_rect)
            r_txt = QGraphicsTextItem(str(v2))
            r_txt.setFont(QFont("Arial", 14))
            r_txt.setPos(cx + 140 + (60-r_txt.boundingRect().width())/2, cy + (60-r_txt.boundingRect().height())/2)
            self.scene.addItem(r_txt)
            r_label = QGraphicsTextItem(f"右: {v2}")
            r_label.setPos(cx+140, cy-25)
            self.scene.addItem(r_label)

            # 中间操作符
            op_txt = QGraphicsTextItem(f"{op}")
            op_txt.setFont(QFont("Arial", 30, QFont.Bold))
            op_txt.setPos(cx - op_txt.boundingRect().width()/2, cy)
            self.scene.addItem(op_txt)

        # 4. 底部说明
        info_y = stack_base_y + 60
        if action_text:
            info_bg = QGraphicsRectItem(cx - 350, info_y, 700, 50)
            info_bg.setBrush(QBrush(QColor("#f9f9f9")))
            info_bg.setPen(QPen(QColor("#cccccc"), 1))
            self.scene.addItem(info_bg)
            
            info_item = QGraphicsTextItem(action_text)
            info_item.setFont(QFont("Arial", 14))
            info_item.setDefaultTextColor(QColor("#36025c"))  # 深紫色提示
            info_item.setPos(cx - info_item.boundingRect().width()/2, info_y + 10)
            self.scene.addItem(info_item)

        try:
            self._auto_scale_view(padding=50)
        except Exception:
            pass
    
    def draw_parentheses_matching_demo(self, expression, current_index, stack_elements, action_text, step_type=None):
        """
        绘制括号匹配算法状态
        """
        self.clear_all_visuals()
        self.scene.clear()

        cx, cy = 400, 300
        
        # 1. 绘制顶部的输入字符串
        str_y = cy - 200
        char_w, char_h = 40, 40
        start_x = cx - (len(expression) * char_w) / 2
        
        title = QGraphicsTextItem("输入字符串序列")
        title.setFont(QFont("Arial", 12, QFont.Bold))
        title.setPos(cx - title.boundingRect().width()/2, str_y - 40)
        self.scene.addItem(title)

        for i, char in enumerate(expression):
            x = start_x + i * char_w
            rect = QGraphicsRectItem(x, str_y, char_w, char_h)
            
            # 高亮当前扫描的字符
            if i == current_index:
                rect.setBrush(QBrush(QColor("#ffdfba"))) # 橙色高亮
                rect.setPen(QPen(QColor("red"), 2))
                # 绘制一个小箭头指向它
                arrow_text = QGraphicsTextItem("↑")
                arrow_text.setFont(QFont("Arial", 14, QFont.Bold))
                arrow_text.setDefaultTextColor(QColor("red"))
                arrow_text.setPos(x + (char_w - arrow_text.boundingRect().width())/2, str_y + char_h)
                self.scene.addItem(arrow_text)
            else:
                rect.setBrush(QBrush(QColor("white")))
                rect.setPen(QPen(QColor("black"), 1))
            
            self.scene.addItem(rect)
            
            txt = QGraphicsTextItem(str(char))
            txt.setFont(QFont("Arial", 14))
            txt.setPos(x + (char_w - txt.boundingRect().width())/2, str_y + (char_h - txt.boundingRect().height())/2)
            self.scene.addItem(txt)
            
            # 索引下标
            idx_txt = QGraphicsTextItem(str(i))
            idx_txt.setFont(QFont("Arial", 8))
            idx_txt.setDefaultTextColor(QColor("gray"))
            idx_txt.setPos(x + (char_w - idx_txt.boundingRect().width())/2, str_y - 15)
            self.scene.addItem(idx_txt)

        # 2. 绘制左侧：栈演示
        stack_x = cx
        stack_base_y = cy + 150
        box_w, box_h = 60, 40
        
        stack_title = QGraphicsTextItem("符号栈")
        stack_title.setFont(QFont("Arial", 12, QFont.Bold))
        stack_title.setDefaultTextColor(QColor("#007acc"))
        stack_title.setPos(stack_x - stack_title.boundingRect().width()/2, stack_base_y + 10)
        self.scene.addItem(stack_title)
        
        base_line = QGraphicsLineItem(stack_x - 50, stack_base_y, stack_x + 50, stack_base_y)
        base_line.setPen(QPen(QColor("black"), 3))
        self.scene.addItem(base_line)

        # 绘制栈元素
        n = len(stack_elements)  # 获取当前栈的总长度
        for i, val in enumerate(stack_elements):
            # i=0 是最老的元素，i=n-1 是最新的元素
            # 我们希望最新的元素 (i=n-1) 在最下面 (level=1)
            # 最老的元素 (i=0) 被顶到最上面 (level=n)
            level = n - i

            rect = QGraphicsRectItem(stack_x - box_w/2, stack_base_y - level*box_h, box_w, box_h)
            rect.setBrush(QBrush(QColor("#a2d2ff")))
            rect.setPen(QPen(QColor("black"), 1))
            self.scene.addItem(rect)
            
            txt = QGraphicsTextItem(str(val))
            txt.setFont(QFont("Arial", 14))
            txt.setPos(stack_x - txt.boundingRect().width()/2, stack_base_y - level*box_h + (box_h - txt.boundingRect().height())/2)
            self.scene.addItem(txt)

        # 3. 底部状态栏
        info_y = stack_base_y + 60
        if action_text:
            color = "#f9f9f9"
            if step_type in ("error", "error_mismatch", "error_unbalanced"):
                color = "#ffcccc"
            elif step_type in ("match", "done_success"):
                color = "#ccffcc"
                
            info_bg = QGraphicsRectItem(cx - 350, info_y, 700, 50)
            info_bg.setBrush(QBrush(QColor(color)))
            info_bg.setPen(QPen(QColor("#cccccc"), 1))
            self.scene.addItem(info_bg)
            
            info_item = QGraphicsTextItem(action_text)
            info_item.setFont(QFont("Arial", 14))

            info_item.setDefaultTextColor(QColor("#36025c"))

            info_item.setPos(cx - info_item.boundingRect().width()/2, info_y + 10)
            self.scene.addItem(info_item)

        try:
            self._auto_scale_view(padding=50)
        except Exception:
            pass
            
    def clear_cached_right_box(self):
        """移除缓存的右上角信息框（如果存在）"""
        try:
            if hasattr(self, '_cached_right_box') and self._cached_right_box is not None:
                rect_item, text_item = self._cached_right_box
                try:
                    self.scene.removeItem(rect_item)
                except Exception:
                    pass
                try:
                    self.scene.removeItem(text_item)
                except Exception:
                    pass
                self._cached_right_box = None
            if hasattr(self, '_cached_right_box_origin'):
                self._cached_right_box_origin = None
        except Exception:
            pass
        # 保证画布刷新
        try:
            self.scene.setSceneRect(self.scene.itemsBoundingRect())
        except Exception:
            pass
        try:
            self.scene.update()
        except Exception:
            pass
        try:
            self.canvas.viewport().update()
        except Exception:
            pass

    def clear_all_visuals(self):
        """
        清除画布上的所有可视化内容，包括任何缓存的信息框或文本
        """
        try:
            # 如果有缓存的右上角信息框，则移除它
            try:
                self.clear_cached_right_box()
            except Exception:
                pass

            # 移除任何其他缓存的信息项或文本
            try:
                if hasattr(self, '_cached_info_item') and self._cached_info_item is not None:
                    try:
                        self.scene.removeItem(self._cached_info_item)
                    except Exception:
                        pass
                    self._cached_info_item = None
            except Exception:
                pass

            try:
                if hasattr(self, '_cached_info_text'):
                    self._cached_info_text = None
            except Exception:
                pass

            try:
                self.scene.clear()
            except Exception:
                pass
            try:
                self.scene.setSceneRect(self.scene.itemsBoundingRect())
            except Exception:
                pass
            try:
                self.scene.update()
            except Exception:
                pass
            try:
                self.canvas.viewport().update()
            except Exception:
                pass
        except Exception:
            pass

    def _get_cached_box_scene_rect(self):
        """
        返回缓存的右上角信息框的场景边界矩形（如果存在且有效），否则返回 None
        """
        try:
            if hasattr(self, '_cached_right_box') and self._cached_right_box:
                rect_item, text_item = self._cached_right_box
                # 确保该项仍在场景中
                if rect_item.scene() is None:
                    try:
                        self._cached_right_box = None
                    except Exception:
                        pass
                    return None
                return rect_item.sceneBoundingRect()
        except Exception:
            pass
        return None

    def display_info_text(self, text: str, color: QColor = QColor("lightgray"), origin: str = None):
        """
        在画布的右上角显示一个信息框，包含给定的文本和颜色
        """
        # 移除缓存的右上角信息框（如果存在）
        try:
            self.clear_cached_right_box()
        except Exception:
            pass

        # 创建文本项
        text_item = QGraphicsTextItem(text)
        text_item.setFont(QFont("Arial", 12))
        text_item.setDefaultTextColor(color)

        # 计算包围盒尺寸并添加内边距
        padding = 10
        br = text_item.boundingRect()
        box_w = br.width() + 2 * padding
        box_h = br.height() + 2 * padding

        # 计算放置位置：右上角，距离视口边缘10像素
        try:
            view_w = self.canvas.viewport().width()
            view_h = self.canvas.viewport().height()
            top_right_in_view = self.canvas.mapToScene(view_w - 10, 10)

            rect_x = top_right_in_view.x() - box_w
            rect_y = top_right_in_view.y()
        except Exception:
            rect_x, rect_y = 2, 2

        rect_item = QGraphicsRectItem(rect_x, rect_y, box_w, box_h)
        rect_item.setBrush(QBrush(QColor("#f2f2f2")))
        rect_item.setPen(QPen(QColor("#cccccc"), 1))

        # 放置文本项在矩形内，考虑内边距
        text_item.setPos(rect_x + padding, rect_y + padding)

        # 添加到场景并缓存引用
        try:
            self.scene.addItem(rect_item)
            self.scene.addItem(text_item)
            self._cached_right_box = (rect_item, text_item)
            if origin is not None:
                self._cached_right_box_origin = origin
            else:
                self._cached_right_box_origin = None
        except Exception:
            try:
                fallback = QGraphicsTextItem(text)
                fallback.setFont(QFont("Arial", 12))
                fallback.setDefaultTextColor(QColor("lightgray"))
                fallback.setPos(2, 2)
                self.scene.addItem(fallback)
                self._cached_info_item = fallback
            except Exception:
                pass
        try:
            self.scene.setSceneRect(self.scene.itemsBoundingRect())
        except Exception:
            pass
        try:
            self.scene.update()
        except Exception:
            pass
        try:
            self.canvas.viewport().update()
        except Exception:
            pass
    
    def draw_linked_list(self, elements: list, highlight_index=None, reconnect_info=None, insert_info=None):
        """
        根据给定的列表数据，在画布上绘制链表

        遍历数据，画节点 (方框 + 文字)
        遍历节点，画连线 (直线 + 箭头)
        如果是插入演示，画绿色的插入箭头
        如果是删除演示，画红色的重连弧线
        """

        # 清除缓存等
        try:
            self.clear_cached_right_box()
        except Exception:
            pass
        self.scene.clear()

        if not elements:
            return

        x_offset, y_offset = 50, 100
        try:
            if hasattr(self, '_cached_right_box') and self._cached_right_box is not None:
                rect_item, _ = self._cached_right_box
                try:
                    box_scene_rect = rect_item.sceneBoundingRect()
                    y_offset = int(box_scene_rect.bottom() + 12 + 20)
                    x_offset = max(20, int(box_scene_rect.left() - 160))
                except Exception:
                    pass
        except Exception:
            pass
        box_width, box_height = 70, 50
        arrow_spacing = 60 # 节点间的箭头长度

        node_items = []  # 存放 (rect, center_x, center_y)

        # 仅在 relink 阶段才实际改变布局/跳过原始 prev->next 箭头，
        # 否则 place 阶段应保持与普通渲染一致（不要留下空隙）
        insert_prev_idx = None
        if insert_info and insert_info.get('phase') == 'relink':
            try:
                insert_prev_idx = insert_info.get('prev')
                # 如果是头插（prev 为 None），把 insert_prev_idx 设为 -1
                # 这样后续的节点会整体右移，腾出插入位置的空间，行为与非头插一致
                if insert_prev_idx is None:
                    insert_prev_idx = -1
            except Exception:
                insert_prev_idx = None

        for i, value in enumerate(elements):
            # 为了在插入可视化时显示明显的缝隙，我们临时把插入位置之后的节点右移一段距离
            extra_shift = 0
            if insert_prev_idx is not None and i > insert_prev_idx:
                # 右移一个节点宽度以腾出空间（可以根据需要调整）
                extra_shift = box_width + 10

            x = x_offset + i * (box_width + arrow_spacing) + extra_shift

            rect = QGraphicsRectItem(x, y_offset, box_width, box_height)
            # 如果被高亮（查询或遍历位置），使用黄色背景并红色边框
            if highlight_index is not None and i == highlight_index:
                rect.setBrush(QBrush(QColor("#fff3b0")))
                rect.setPen(QPen(QColor("red"), 3))
            else:
                rect.setBrush(QBrush(QColor("#70806d")))
            self.scene.addItem(rect)
            
            text = QGraphicsTextItem(str(value))
            text.setFont(QFont("Arial", 14))
            # 链表节点文本使用深紫色
            text.setDefaultTextColor(QColor("#4B0082"))
            text_x = x + (box_width - text.boundingRect().width()) / 2
            text_y = y_offset + (box_height - text.boundingRect().height()) / 2
            text.setPos(text_x, text_y)
            self.scene.addItem(text)
            # 在每个链表节点下面绘制索引标签，便于教学演示
            idx_text = QGraphicsTextItem(str(i))
            idx_text.setFont(QFont("Arial", 10))
            idx_text.setDefaultTextColor(QColor("lightgray"))
            idx_x = x + (box_width - idx_text.boundingRect().width()) / 2
            idx_y = y_offset + box_height + 6
            idx_text.setPos(idx_x, idx_y)
            self.scene.addItem(idx_text)
            
            center_x = x + box_width / 2
            center_y = y_offset + box_height / 2
            node_items.append((rect, center_x, center_y))

        pen = QPen(Qt.black, 2)
        pen.setWidth(2)

        # 绘制正常的 next 指针（箭头）
        for i in range(len(node_items) - 1):
            start_node, sx, sy = node_items[i]
            end_node, ex, ey = node_items[i+1]

            start_x = start_node.rect().right()
            start_y = start_node.rect().center().y()
            end_x = end_node.rect().left()
            end_y = end_node.rect().center().y()

            # 如果当前为插入演示并且这是 prev->next 原始箭头，则跳过绘制，
            # 我们将在插入处理代码中绘制 prev->new 和 new->next
            if insert_prev_idx is not None and i == insert_prev_idx:
                continue
            line = QGraphicsLineItem(start_x, start_y, end_x, end_y)
            line.setPen(pen)
            self.scene.addItem(line)
            
            # 绘制箭头部分
            arrow_size = 10.0
            angle = line.line().angle()

            p1 = line.line().p2()
            arrow_p1 = p1 - QPointF(cos(radians(angle)) * arrow_size + sin(radians(angle)) * arrow_size / 2, 
                                    sin(radians(angle)) * arrow_size - cos(radians(angle)) * arrow_size / 2)
            arrow_p2 = p1 - QPointF(cos(radians(angle)) * arrow_size - sin(radians(angle)) * arrow_size / 2, 
                                    sin(radians(angle)) * arrow_size + cos(radians(angle)) * arrow_size / 2)

            arrow_head = QPolygonF([p1, arrow_p1, arrow_p2])
            arrow_item = QGraphicsPolygonItem(arrow_head)
            arrow_item.setBrush(Qt.black)
            self.scene.addItem(arrow_item)

        # 如果需要显示插入(insert)信息，在目标缝隙处临时留出空间并绘制新节点与延长的箭头
        if insert_info:
            try:
                at_idx = insert_info.get('at')
                val = insert_info.get('value')
                prev_idx = insert_info.get('prev')
                next_idx = insert_info.get('next')
                phase = insert_info.get('phase')

                # 计算新节点放置位置：放在 prev 和 next 的中间横坐标上（与其他节点同一行）
                if prev_idx is not None and 0 <= prev_idx < len(node_items):
                    _, px, py = node_items[prev_idx]
                    prev_right = node_items[prev_idx][0].rect().right()
                else:
                    px = None
                    prev_right = x_offset

                if next_idx is not None and 0 <= next_idx < len(node_items):
                    _, nx, ny = node_items[next_idx]
                    next_left = node_items[next_idx][0].rect().left()
                else:
                    nx = None
                    # place to the right of last node
                    next_left = (node_items[-1][0].rect().right() + box_width + arrow_spacing) if node_items else x_offset + box_width

                # 仅在 relink 阶段绘制可视化（用户要求只保留带有文字的步骤展示）。
                # 在 'place' 阶段我们不再绘制临时节点/箭头，避免重复的静态截图状态。
                if phase == 'relink':
                    # 绘制 prev 为 None（头插）时的 head_rect 以便后续把新节点居中在 head 和第0号节点之间
                    arrow_pen = QPen(QColor("green"), 2)
                    arrow_pen.setWidth(2)

                    if prev_idx is None:
                        try:
                            first_rect = node_items[0][0]
                            # 将 head 放得更远一些，这里使用 2 倍的 arrow_spacing，使 head 与 0 号节点间距更明显
                            head_x = first_rect.rect().left() - (box_width + 2 * arrow_spacing)
                        except Exception:
                            head_x = x_offset - (box_width + 2 * arrow_spacing)
                        head_y = y_offset
                        head_rect = QGraphicsRectItem(head_x, head_y, box_width, box_height)
                        head_rect.setBrush(QBrush(QColor("#fff3b0")))
                        head_rect.setPen(QPen(QColor("#cfa800"), 2))
                        self.scene.addItem(head_rect)

                        head_label = QGraphicsTextItem("头节点")
                        head_label.setFont(QFont("Arial", 10, QFont.Bold))
                        head_label.setDefaultTextColor(QColor("#36025c"))
                        hl_x = head_x + (box_width - head_label.boundingRect().width()) / 2
                        hl_y = head_y + (box_height - head_label.boundingRect().height()) / 2
                        head_label.setPos(hl_x, hl_y)
                        self.scene.addItem(head_label)

                        # 把 prev_right 设为 head_rect 的右侧，这样 new 会在 head 与 next 之间居中
                        prev_right = head_rect.rect().right()

                    # 计算新节点中心位置
                    new_center_x = (prev_right + next_left) / 2
                    # 将临时新节点绘制得更低一点，以便与原行区分开（更明显的插入感），
                    # 增大垂直偏移以避免箭头遮挡
                    new_center_y = y_offset + box_height / 2 + 36

                    # 绘制放置的节点（偏下的临时新节点）
                    new_x = new_center_x - box_width / 2
                    new_y = new_center_y - box_height / 2
                    new_rect = QGraphicsRectItem(new_x, new_y, box_width, box_height)
                    new_rect.setBrush(QBrush(QColor("#f0f8ff")))
                    new_rect.setPen(QPen(QColor("#4b8bff"), 2))
                    self.scene.addItem(new_rect)

                    new_text = QGraphicsTextItem(str(val))
                    new_text.setFont(QFont("Arial", 14))
                    new_text.setDefaultTextColor(QColor("#4B0082"))
                    new_text.setPos(new_x + (box_width - new_text.boundingRect().width()) / 2,
                                     new_y + (box_height - new_text.boundingRect().height()) / 2)
                    self.scene.addItem(new_text)
                    arrow_size = 10.0

                    def draw_straight_arrow(sx, sy, ex, ey, pen):
                        line = QGraphicsLineItem(sx, sy, ex, ey)
                        line.setPen(pen)
                        self.scene.addItem(line)
                        ang = atan2(ey - sy, ex - sx)
                        left = QPointF(ex - cos(ang - pi/6) * arrow_size,
                                       ey - sin(ang - pi/6) * arrow_size)
                        right = QPointF(ex - cos(ang + pi/6) * arrow_size,
                                        ey - sin(ang + pi/6) * arrow_size)
                        arrow_head = QPolygonF([QPointF(ex, ey), left, right])
                        arrow_item = QGraphicsPolygonItem(arrow_head)
                        arrow_item.setBrush(pen.color())
                        self.scene.addItem(arrow_item)

                    # prev -> new
                    # 如果是头插，绘制 head -> new
                    if prev_idx is None:
                        try:
                            sx = head_rect.rect().right()
                            sy = head_rect.rect().center().y()
                            ex = new_rect.rect().left()
                            ey = new_rect.rect().center().y()
                            draw_straight_arrow(sx, sy, ex, ey, arrow_pen)
                        except Exception:
                            pass

                    if prev_idx is not None and 0 <= prev_idx < len(node_items):
                        prev_rect = node_items[prev_idx][0]
                        sx = prev_rect.rect().right()
                        sy = prev_rect.rect().center().y()
                        ex = new_rect.rect().left()
                        ey = new_rect.rect().center().y()
                        draw_straight_arrow(sx, sy, ex, ey, arrow_pen)

                    # new -> next
                    if next_idx is not None and 0 <= next_idx < len(node_items):
                        next_rect = node_items[next_idx][0]
                        sx = new_rect.rect().right()
                        sy = new_rect.rect().center().y()
                        ex = next_rect.rect().left()
                        ey = next_rect.rect().center().y()
                        draw_straight_arrow(sx, sy, ex, ey, arrow_pen)

                    # 在 relink 阶段显示文本标签
                    label = QGraphicsTextItem("插入")
                    label.setDefaultTextColor(QColor("green"))
                    label.setFont(QFont("Arial", 10, QFont.Bold))
                    label.setPos(new_center_x - label.boundingRect().width()/2, new_y - 18)
                    self.scene.addItem(label)

            except Exception:
                pass

        # 如果需要显示重连(reconnect)信息，在 prev->next 之间画一条红色的弧线并显示标签
        if reconnect_info:
            try:
                prev_idx = reconnect_info.get("prev")
                next_idx = reconnect_info.get("next")
                at_idx = reconnect_info.get("at")
                # 标记被删除的节点（位于 at_idx）为浅灰表示待删除
                if at_idx is not None and 0 <= at_idx < len(node_items):
                    rect_item, cx, cy = node_items[at_idx]
                    rect_item.setBrush(QBrush(QColor("#d3d3d3")))

                if prev_idx is None:
                    # 如果 prev 为 None，说明删除的是头节点：用弧线从被删除节点左侧连向新的头
                    if next_idx is not None and 0 <= next_idx < len(node_items):
                        _, nx, ny = node_items[next_idx]
                        # 绘制一个临时的“头指针/头节点”方框在第一个节点左侧，颜色为黄色并标注“头节点”。
                        try:
                            first_rect = node_items[0][0]
                            # 与插入时保持一致的更大间距
                            head_x = first_rect.rect().left() - (box_width + arrow_spacing + 10)
                        except Exception:
                            # 兜底：使用画布的左边作为 head 的位置
                            head_x = x_offset - (box_width + arrow_spacing + 10)
                        head_y = y_offset
                        head_rect = QGraphicsRectItem(head_x, head_y, box_width, box_height)
                        head_rect.setBrush(QBrush(QColor("#fff3b0")))
                        head_rect.setPen(QPen(QColor("#cfa800"), 2))
                        self.scene.addItem(head_rect)

                        head_label = QGraphicsTextItem("头节点")
                        head_label.setFont(QFont("Arial", 10, QFont.Bold))
                        head_label.setDefaultTextColor(QColor("#36025c"))
                        hl_x = head_x + (box_width - head_label.boundingRect().width()) / 2
                        hl_y = head_y + (box_height - head_label.boundingRect().height()) / 2
                        head_label.setPos(hl_x, hl_y)
                        self.scene.addItem(head_label)

                        # 从 head_rect 的下方开始绘制弧线，指向新的头节点
                        start_x = head_rect.rect().right()
                        start_y = head_rect.rect().bottom() + 10
                        end_x = nx - box_width/2
                        end_y = ny + box_height/2 + 10
                        # 使用二次贝塞尔曲线画弧线
                        path = QPainterPath(QPointF(start_x, start_y))
                        mid_x = (start_x + end_x) / 2
                        arc_h = 40
                        # 向下弧线：控制点放在两个端点之下
                        control_y = max(start_y, end_y) + arc_h
                        path.quadTo(QPointF(mid_x, control_y), QPointF(end_x, end_y))
                        path_item = QGraphicsPathItem(path)
                        path_item.setPen(QPen(QColor("red"), 2, Qt.DashLine))
                        self.scene.addItem(path_item)
                        # 小箭头，指向 end
                        # 计算二次贝塞尔在终点处的切线方向以确定箭头角度
                        control_pt = QPointF(mid_x, control_y)
                        dx = end_x - control_pt.x()
                        dy = end_y - control_pt.y()
                        angle = atan2(dy, dx)
                        arrow_size = 10.0
                        # 箭头两个基点相对于终点，偏移角度为±30度
                        left = QPointF(end_x - cos(angle - pi/6) * arrow_size,
                                       end_y - sin(angle - pi/6) * arrow_size)
                        right = QPointF(end_x - cos(angle + pi/6) * arrow_size,
                                        end_y - sin(angle + pi/6) * arrow_size)
                        arrow_head = QPolygonF([QPointF(end_x, end_y), left, right])
                        arrow_item = QGraphicsPolygonItem(arrow_head)
                        arrow_item.setBrush(QColor("red"))
                        self.scene.addItem(arrow_item)
                else:
                    # 常规 prev -> next 的重连，在两个节点下方画一条红色弧线
                    if 0 <= prev_idx < len(node_items) and 0 <= next_idx < len(node_items):
                        _, px, py = node_items[prev_idx]
                        _, nx, ny = node_items[next_idx]
                        start_x = px + box_width/2
                        start_y = py + box_height/2 + 10
                        end_x = nx - box_width/2
                        end_y = ny + box_height/2 + 10
                        # 使用二次贝塞尔曲线画弧线，弧顶在两个节点上方
                        path = QPainterPath(QPointF(start_x, start_y))
                        mid_x = (start_x + end_x) / 2
                        arc_h = 40
                        # 向下弧线：控制点放在两个端点之下
                        control_y = max(start_y, end_y) + arc_h
                        path.quadTo(QPointF(mid_x, control_y), QPointF(end_x, end_y))
                        path_item = QGraphicsPathItem(path)
                        path_item.setPen(QPen(QColor("red"), 2, Qt.DashLine))
                        self.scene.addItem(path_item)

                        # 绘制箭头头（简单三角形，放在弧线终点）
                        # 计算二次贝塞尔在终点处的切线方向以确定箭头角度
                        control_pt = QPointF(mid_x, control_y)
                        dx = end_x - control_pt.x()
                        dy = end_y - control_pt.y()
                        angle = atan2(dy, dx)
                        arrow_size = 10.0
                        left = QPointF(end_x - cos(angle - pi/6) * arrow_size,
                                       end_y - sin(angle - pi/6) * arrow_size)
                        right = QPointF(end_x - cos(angle + pi/6) * arrow_size,
                                        end_y - sin(angle + pi/6) * arrow_size)
                        arrow_head = QPolygonF([QPointF(end_x, end_y), left, right])
                        arrow_item = QGraphicsPolygonItem(arrow_head)
                        arrow_item.setBrush(QColor("red"))
                        self.scene.addItem(arrow_item)

                        # 在重连线上显示文本标签
                        label = QGraphicsTextItem("重连")
                        label.setDefaultTextColor(QColor("red"))
                        label.setFont(QFont("Arial", 10, QFont.Bold))
                        mid_x = (start_x + end_x) / 2
                        # 文本放在弧线下方，稍微离开弧线以避免重叠
                        # 将文本稍微上移 5 像素以避免与弧线或箭头重叠
                        label.setPos(mid_x - label.boundingRect().width()/2, control_y + 7)
                        self.scene.addItem(label)
            except Exception:
                pass

        try:
            self._auto_scale_view(padding=60, min_scale=0.1)
        except Exception:
            pass

    def draw_stack(self, elements: list, viz: dict = None):
        """
        根据给定的列表数据，绘制栈
        效果：新元素出现在线上方，旧元素被向上推
        """
        try:
            self.clear_cached_right_box()
        except Exception:
            pass
        self.scene.clear()

        try:
            viewport_rect = self.canvas.viewport().rect()

            if hasattr(self, '_cached_right_box') and self._cached_right_box is not None:
                rect_item, _ = self._cached_right_box
                try:
                    box_scene_rect = rect_item.sceneBoundingRect()
                    margin = 40
                    x_center = box_scene_rect.left() - margin
                except Exception:
                    center_view = viewport_rect.center()
                    center_scene = self.canvas.mapToScene(center_view)
                    x_center = center_scene.x()
            else:
                center_view = viewport_rect.center()
                center_scene = self.canvas.mapToScene(center_view)
                x_center = center_scene.x()
        except Exception:
            x_center = self.canvas.width() / 2
        # 将基准线放在靠近右上角提示文本框的位置（如果存在），
        # 这样栈的纵向位置会更靠近右上角提示，减少视觉距离。回退到画布底部布局。
        try:
            if hasattr(self, '_cached_right_box') and self._cached_right_box is not None:
                rect_item, _ = self._cached_right_box
                box_scene_rect = rect_item.sceneBoundingRect()

                base_y = box_scene_rect.bottom() + 80
            else:
                try:
                    base_y = self.canvas.viewport().height() / 2 + 100
                except Exception:
                    base_y = self.canvas.height() / 2 + 100
        except Exception:
            base_y = self.canvas.height() + 100
        box_width = 80
        box_height = 50
        spacing = 5

        # 绘制栈的基准线
        base_line = QGraphicsLineItem(x_center - box_width, base_y + 5, x_center + box_width, base_y + 5)
        # 改为用户指定的入口线颜色
        base_line.setPen(QPen(QColor("#00ffb3"), 3))
        self.scene.addItem(base_line)

        # 在基准线旁边标注“栈顶”，颜色为绿色
        try:
            top_label = QGraphicsTextItem("栈顶")
            top_label.setFont(QFont("Arial", 12, QFont.Bold))
            top_label.setDefaultTextColor(QColor("#baed5b"))
            label_x = x_center + box_width + 10
            label_y = base_y - box_height / 2
            top_label.setPos(label_x, 30 + label_y - top_label.boundingRect().height() / 2)
            self.scene.addItem(top_label)
        except Exception:
            pass
        
        # elements 列表: [oldest, ..., newest]
        # 我们要让 newest 紧贴线上方，oldest 在最顶上
        num_elements = len(elements)
        # 收集每个元素的 rect 和中心坐标，便于之后绘制高亮圈
        elem_items = []
        for i, value in enumerate(elements):
            # i=0 是最老的元素, i=num_elements-1 是最新的元素
            # 最新的元素(i=num_elements-1) 应该离基准线最近 (y坐标最大)
            # 最老的元素(i=0) 应该离基准线最远 (y坐标最小)
            
            # (num_elements - 1 - i) 这个计算可以得到反向的索引
            # i=0时, 值为 num_elements-1 (最远)
            # i=num_elements-1时, 值为0 (最近)
            y_pos_index = num_elements - 1 - i
            
            y = base_y - (y_pos_index + 1) * (box_height + spacing) + spacing
            x = x_center - box_width / 2
            
            # 绘制方块
            rect_item = QGraphicsRectItem(x, y, box_width, box_height)
            rect_item.setBrush(QBrush(QColor("#ffc8dd")))
            self.scene.addItem(rect_item)
            
            # 绘制文本
            text_item = QGraphicsTextItem(str(value))
            text_item.setFont(QFont("Arial", 14))
            # 栈中节点文本使用深紫色
            text_item.setDefaultTextColor(QColor("#36025c"))
            text_x = x + (box_width - text_item.boundingRect().width()) / 2
            text_y = y + (box_height - text_item.boundingRect().height()) / 2
            text_item.setPos(text_x, text_y)
            self.scene.addItem(text_item)
            # 记录元素信息
            elem_items.append((rect_item, x, y, x + box_width / 2, y + box_height / 2))

        # 处理短暂的可视化提示（由 controller 通过 viz 传入）
        try:
            if viz:
                # 高亮栈顶（红圈）
                if viz.get('highlight_top') and elem_items:
                    rect, rx, ry, cx, cy = elem_items[-1]
                    # 用带边框的矩形高亮栈顶元素（红色）
                    padding = 6
                    hx = rx - padding
                    hy = ry - padding
                    hw = box_width + padding * 2
                    hh = box_height + padding * 2
                    highlight_rect = QGraphicsRectItem(hx, hy, hw, hh)
                    highlight_rect.setPen(QPen(QColor("red"), 3))
                    highlight_rect.setBrush(QBrush(QColor(255, 0, 0, 40)))
                    self.scene.addItem(highlight_rect)

                # 新 push 的元素（蓝圈）
                if 'pushed_index' in viz and elem_items:
                    idx = viz.get('pushed_index')
                    if 0 <= idx < len(elem_items):
                        rect, rx, ry, cx, cy = elem_items[idx]
                        # 用带边框的矩形高亮被 push 的元素（蓝色）
                        padding = 6
                        hx = rx - padding
                        hy = ry - padding
                        hw = box_width + padding * 2
                        hh = box_height + padding * 2
                        highlight_rect = QGraphicsRectItem(hx, hy, hw, hh)
                        highlight_rect.setPen(QPen(QColor("blue"), 3))
                        highlight_rect.setBrush(QBrush(QColor(0, 0, 255, 40)))
                        self.scene.addItem(highlight_rect)

                # 被 pop 出去的元素：在栈右侧绘制一个单独的方框，放置在与被弹出元素同一高度的偏移位置
                if 'popped_value' in viz:
                    pv = viz.get('popped_value')
                    p_idx = viz.get('popped_from_index', None)
                    # 计算绘制位置：靠右，距离栈体一定偏移
                    out_x = x_center + box_width + 80
                    if p_idx is None:
                        # 若不知道原索引，将其画在基准线附近
                        out_y = base_y - box_height - 10
                    else:
                        # 使用与元素相同的排列计算 y 坐标
                        y_pos_index = num_elements - 1 - p_idx
                        out_y = base_y - (y_pos_index + 1) * (box_height + spacing) + spacing
                    popped_rect = QGraphicsRectItem(out_x, out_y, box_width, box_height)
                    popped_rect.setBrush(QBrush(QColor("#e0e0e0")))
                    popped_rect.setPen(QPen(QColor("#555555"), 2))
                    self.scene.addItem(popped_rect)
                    popped_text = QGraphicsTextItem(str(pv))
                    popped_text.setFont(QFont("Arial", 14))
                    popped_text.setDefaultTextColor(QColor("#36025c"))
                    pt_x = out_x + (box_width - popped_text.boundingRect().width()) / 2
                    pt_y = out_y + (box_height - popped_text.boundingRect().height()) / 2
                    popped_text.setPos(pt_x, pt_y)
                    self.scene.addItem(popped_text)
        except Exception:
            # 保持稳健，任何可视化失败都不应阻塞主视图
            pass
        try:
            self._auto_scale_view()
        except Exception:
            pass

    def draw_b_tree(self, root_node, info_text=None):
        """
        绘制 B-树 的简单可视化。节点为水平排列的键框，子节点位于下方。
        该实现比较保守，主要用于展示节点分裂和键分布。
        """
        try:
            self.clear_cached_right_box()
        except Exception:
            pass
        self.scene.clear()

        # 如果有解释文本，绘制右上角文本框
        if info_text:
            try:
                # 使用深蓝色文本显示 B-树 说明信息
                self.draw_right_text_box(info_text, QColor("#0056b3"))
            except Exception:
                pass

        if not root_node:
            return

        # 先测量树的布局（返回每个节点的宽度）
        positions = {}
        sizes = {}
        try:
            total_w = self._measure_btree(root_node, positions, sizes)
        except Exception:
            # 如果测量失败，回退到简单的线性布局
            positions = {root_node: (0, 0)}
            sizes = {root_node: (120, 40)}

        # 计算左上起点使树居中
        try:
            view_w = self.canvas.viewport().width()
            start_x = max(20, (view_w - total_w) / 2)
        except Exception:
            start_x = 20

        # 将测量的横向偏移应用为最终坐标
        x_cursor = start_x
        y_base = 80
        # 递归绘制并连接
        self._draw_btree_recursive(root_node, x_cursor, y_base, positions, sizes)

        try:
            self._auto_scale_view(padding=60, min_scale=0.1)
        except Exception:
            pass

    def show_b_tree_info(self, t):
        """
        显示B树的阶数定义图示，并在2秒后自动隐藏
        """
        # 设置图片路径（可以按需修改为项目中实际的图片路径）
        import os
        from PySide6.QtCore import Qt, QTimer
        # 默认相对路径（相对于项目根）——请根据实际文件调整
        image_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'aaa数据结构课设', 'B树函数.svg')
        # 兼容简单相对路径尝试
        if not os.path.exists(image_path):
            image_path = os.path.join(os.getcwd(), 'B树函数.svg')

        try:
            if os.path.exists(image_path):
                pixmap = QPixmap(image_path)
                # 缩放图片以适应宽度
                scaled_pixmap = pixmap.scaledToWidth(400, Qt.Mode.SmoothTransformation)
                self.image_label.setPixmap(scaled_pixmap)
                # 显示控件
                self.image_label.show()
                # 2秒后自动隐藏
                try:
                    QTimer.singleShot(2000, self.image_label.hide)
                except Exception:
                    # 退化方案：几毫秒后再隐藏，避免在某些 PySide 版本上出错
                    try:
                        QTimer.singleShot(2000, lambda: self.image_label.setVisible(False))
                    except Exception:
                        pass
            else:
                # 如果图片不存在，则在右侧用文本替代（不阻塞）
                self.image_label.setText(f"B-树 (t={t})")
                self.image_label.show()
                try:
                    QTimer.singleShot(2000, self.image_label.hide)
                except Exception:
                    pass
        except Exception:
            pass

    def _measure_btree(self, node, positions, sizes, key_box_w=30, padding=8):
        """
        测量 B-树 子树宽度并填充 `positions` 与 `sizes`。
        返回此子树的所需总宽度（用于父级布局）。
        """
        if node is None:
            return 0

        # 叶子：宽度由键数量决定
        num_keys = len(node.keys)
        node_w = max(60, num_keys * key_box_w + (num_keys - 1) * padding)
        child_widths = []
        if hasattr(node, 'children') and node.children:
            # 递归测量每个孩子
            for c in node.children:
                w = self._measure_btree(c, positions, sizes, key_box_w, padding)
                child_widths.append(w)

        # 如果有孩子，总宽度至少是孩子总宽
        if child_widths:
            total_children_w = sum(child_widths) + max(0, len(child_widths) - 1) * padding
            total_w = max(node_w, total_children_w)
        else:
            total_w = node_w

        # 缓存一个相对宽度（具体 x 位置在绘制时决定）
        sizes[node] = (node_w, 40)
        positions[node] = (total_w, 0)  # 临时占位，实际 x 在绘制中使用
        return total_w

    def _draw_btree_recursive(self, node, x_start, y, positions, sizes, padding=12, level_gap=80):
        """
        在 scene 上绘制节点并递归绘制子节点。
        x_start 为当前子树的左起点。
        """
        if node is None:
            return 0

        node_w, node_h = sizes.get(node, (120, 40))
        # 如果有孩子，按孩子宽度分配空间并居中父节点
        child_ws = []
        children = getattr(node, 'children', []) or []
        for c in children:
            cw = sizes.get(c, (120, 40))[0]
            child_ws.append(cw)

        if child_ws:
            total_children_w = sum(child_ws) + (len(child_ws) - 1) * padding
            # 父节点横向居中于子树上方
            parent_x = x_start + (total_children_w - node_w) / 2
        else:
            total_children_w = node_w
            parent_x = x_start

        # 绘制父节点盒子（包含所有键）
        box = QGraphicsRectItem(parent_x, y, node_w, node_h)
        box.setBrush(QBrush(QColor("#fde4cf")))
        box.setPen(QPen(QColor("#4B0082"), 1))
        self.scene.addItem(box)

        # 绘制键文本，水平分布
        keys = getattr(node, 'keys', [])
        if keys:
            key_gap = node_w / max(1, len(keys))
            # 绘制键之间的分隔线
            for i in range(len(keys) - 1):
                # 分隔线位置：当前起点 + (i+1) * 每个格子的宽度
                line_x = parent_x + (i + 1) * key_gap
                # 绘制竖线：从节点顶部(y) 到 底部(y+node_h)
                sep_line = QGraphicsLineItem(line_x, y, line_x, y + node_h)
                sep_line.setPen(QPen(QColor("#4B0082"), 1))
                self.scene.addItem(sep_line)

            for i, k in enumerate(keys):
                tx = parent_x + i * key_gap + (key_gap - QGraphicsTextItem(str(k)).boundingRect().width()) / 2
                ty = y + (node_h - QGraphicsTextItem(str(k)).boundingRect().height()) / 2
                t = QGraphicsTextItem(str(k))
                t.setFont(QFont("Arial", 12))
                t.setDefaultTextColor(QColor("#4B0082"))
                t.setPos(tx, ty)
                self.scene.addItem(t)

        # 递归绘制孩子并链接
        child_x = x_start
        child_y = y + node_h + level_gap
        for idx, c in enumerate(children):
            cw = sizes.get(c, (120, 40))[0]
            # 绘制子树并获取子宽度
            self._draw_btree_recursive(c, child_x, child_y, positions, sizes, padding, level_gap)

            # 计算父中心与子中心以绘制连接线
            child_center_x = child_x + cw / 2
            parent_center_x = parent_x + node_w / 2
            line = QGraphicsLineItem(parent_center_x, y + node_h, child_center_x, child_y)
            line.setPen(QPen(QColor("#ADD8E6"), 2))
            self.scene.addItem(line)

            child_x += cw + padding


    def draw_huffman_build_step(self, state):
        """绘制哈夫曼树构建的单步状态"""
        try:
            self.clear_cached_right_box()
        except Exception:
            pass
        self.scene.clear()
        if not state: return

        queue_nodes = state.get("queue", [])
        merged_tree = state.get("merged_tree")
        final_tree = state.get("tree")
        highlight_nodes = state.get("highlight_nodes", [])
        text = state.get("text", "")

        # 绘制最终完成的树
        if final_tree:
            self.draw_huffman_tree(final_tree, state.get("codes"))
            if text: self.draw_right_text_box(text, QColor("green"))
            return

        # 绘制队列中的所有节点/子树
        all_nodes_on_canvas = []
        if queue_nodes: all_nodes_on_canvas.extend(queue_nodes)
        if merged_tree: all_nodes_on_canvas.append(merged_tree)
        
        # 使用一个简单的水平布局来放置所有独立的树/节点
        x_cursor = 30

        y_pos = 100
        node_radius = 25
        h_spacing = 40 # 增加水平间距以避免高亮重叠

        for root in all_nodes_on_canvas:
            positions = {}
            self._get_node_positions(root, positions, use_id=True)
            
            # 偏移当前树的所有节点
            min_x = min(pos[0] for pos in positions.values()) if positions else 0
            offset_x = x_cursor - min_x

            offset_positions = {key: (val[0] + offset_x, val[1] + y_pos) for key, val in positions.items()}

            # 绘制
            is_highlighted = any(id(root) == id(hn) for hn in highlight_nodes)
            self._draw_bst_edges(root, offset_positions, use_id=True)
            self._draw_huffman_nodes(root, offset_positions, {}, is_highlighted)
            
            # 更新下一个树的起始x坐标
            max_x = max(pos[0] + node_radius for pos in offset_positions.values()) if offset_positions else x_cursor
            x_cursor = max_x + h_spacing

        if text:
            self.draw_right_text_box(text, QColor("blue"))
        try:
            self._auto_scale_view()
        except Exception:
            pass


    def draw_huffman_tree(self, root_node, codes=None):
        """
        在画布上绘制哈夫曼树，并在右侧显示编码信息
        """
        try:
            self.clear_cached_right_box()
        except Exception:
            pass
        self.scene.clear()
        if not root_node:
            return

        positions = {}
        # 使用 id(node) 作为键来避免哈希问题
        self._get_node_positions(root_node, positions, use_id=True)
        try:
            gap = 8
            used = False
            box_rect = self._get_cached_box_scene_rect()
            if box_rect is not None:
                try:
                    box_left = box_rect.left()
                    # compute tree's current horizontal span
                    xs = [pos[0] for pos in positions.values()]
                    if xs:
                        max_x = max(xs)
                        # shift so tree's right edge is at (box_left - gap)
                        dx = (box_left - gap) - max_x
                        for k, (x, y) in list(positions.items()):
                            positions[k] = (x + dx, y)
                        used = True
                except Exception:
                    used = False

            if not used:
                viewport_rect = self.canvas.viewport().rect()
                center_view = viewport_rect.center()
                center_scene = self.canvas.mapToScene(center_view)

                desired_center_x = center_scene.x() - 10
                xs = [pos[0] for pos in positions.values()]
                if xs:
                    min_x = min(xs)
                    max_x = max(xs)
                    tree_center = (min_x + max_x) / 2
                    dx = desired_center_x - tree_center
                    for k, (x, y) in list(positions.items()):
                        positions[k] = (x + dx, y)
        except Exception:
            pass

        self._draw_bst_edges(root_node, positions, use_id=True)
        self._draw_huffman_nodes(root_node, positions, codes)

        if codes:
            # 在右侧显示编码信息
            info_text = "哈夫曼编码:\n" + "\n".join([f"  {char}: {code}" for char, code in codes.items()])
            
            # 创建一个大的文本块来显示所有编码
            codes_item = QGraphicsTextItem(info_text)
            codes_item.setFont(QFont("Consolas", 14))
            codes_item.setDefaultTextColor(QColor("lightgrey"))
            
            # 将其放置在视图的右上角
            view_width = self.canvas.width()
            text_width = codes_item.boundingRect().width()
            codes_item.setPos(view_width - text_width - 80, 20)
            self.scene.addItem(codes_item)
        try:
            self._auto_scale_view()
        except Exception:
            pass

    def _draw_huffman_nodes(self, node, positions, codes, is_highlighted=False):
        """
        递归绘制哈夫曼树节点
        """
        if not node:
            return
        
        x, y = positions.get(id(node), (0, 0))
        node_radius = 25
        
        # 叶子节点用方形，内部节点用圆形
        if node.char is not None:
            item = QGraphicsRectItem(x - node_radius, y - node_radius, node_radius * 2, node_radius * 2)
            item.setBrush(QBrush(QColor("#9ef01a"))) # 绿色
            display_text = f"{node.char}\n({node.weight})"
        else:
            item = QGraphicsEllipseItem(x - node_radius, y - node_radius, node_radius * 2, node_radius * 2)
            item.setBrush(QBrush(QColor("#fde4cf"))) # 橙色
            display_text = str(node.weight)
        
        if is_highlighted:
            pen = QPen(QColor("red"), 3)
            item.setPen(pen)
            
        self.scene.addItem(item)

        text = QGraphicsTextItem(display_text)
        text.setFont(QFont("Arial", 10, QFont.Bold))
        text_rect = text.boundingRect()
        # 哈夫曼节点文本使用深紫色
        text.setDefaultTextColor(QColor("#36025c"))
        text_x = x - text_rect.width() / 2
        text_y = y - text_rect.height() / 2
        text.setPos(text_x, text_y)
        self.scene.addItem(text)

        self._draw_huffman_nodes(node.left, positions, codes)
        self._draw_huffman_nodes(node.right, positions, codes)

    def draw_bst(self, root_node, highlight_info=None):
        """
        在画布上绘制二叉搜索树（BST）
        还绘制AVL树
        """
        try:
            self.clear_cached_right_box()
        except Exception:
            pass
        self.scene.clear()
        if highlight_info is None:
            highlight_info = {}
            
        if not root_node:
            info_text = highlight_info.get("text", "")
            if info_text:
                self.draw_right_text_box(info_text, QColor("red"))
            return

        positions = {}
        self._get_node_positions(root_node, positions)

        try:
            viewport_rect = self.canvas.viewport().rect()
            center_view = viewport_rect.center()
            center_scene = self.canvas.mapToScene(center_view)
            desired_center_x = center_scene.x() - 10
            xs = [pos[0] for pos in positions.values()]
            if xs:
                min_x = min(xs)
                max_x = max(xs)
                tree_center = (min_x + max_x) / 2
                dx = desired_center_x - tree_center
                for k, (x, y) in list(positions.items()):
                    positions[k] = (x + dx, y)
        except Exception:
            pass

        self._draw_bst_edges(root_node, positions)
        self._draw_bst_nodes(root_node, positions, highlight_info)
        
        info_text = highlight_info.get("text", "")
        if info_text:
            self.draw_right_text_box(info_text, QColor("red"))
        try:
            self._auto_scale_view()
        except Exception:
            pass


    def _get_node_positions(self, node, positions, use_id=False):
        """计算所有节点的坐标并存储在positions字典中"""
        x_map = {}
        self._assign_x(node, x_map, [0], use_id) # 使用列表传递计数器以实现引用传递

        depth_map = {}
        self._assign_depth(node, depth_map, 0, use_id)

        # 增加水平间距以减少节点标签重叠的问题
        h_spacing, v_spacing = 80, 80
        x_offset, y_offset = 30, 140

        for key, x_index in x_map.items():
            depth = depth_map.get(key, 0)
            positions[key] = (x_index * h_spacing + x_offset, depth * v_spacing + y_offset)

    def _assign_x(self, node, x_map, counter, use_id=False):
        """中序遍历以分配X坐标索引"""
        if not node:
            return
        self._assign_x(node.left, x_map, counter, use_id)
        key = id(node) if use_id else node.key
        x_map[key] = counter[0]
        counter[0] += 1
        self._assign_x(node.right, x_map, counter, use_id)

    def _assign_depth(self, node, depth_map, depth, use_id=False):
        """前序遍历以分配深度"""
        if not node:
            return
        key = id(node) if use_id else node.key
        depth_map[key] = depth
        self._assign_depth(node.left, depth_map, depth + 1, use_id)
        self._assign_depth(node.right, depth_map, depth + 1, use_id)

    def _draw_bst_nodes(self, node, positions, highlight_info):
        """
        递归绘制BST节点
        还能求出AVL节点的平衡因子并显示在节点上方
        """
        if not node:
            return

        # 如果该节点在 positions 中没有坐标，则说明它不属于当前要绘制的树（防止绘制陈旧/残留节点）
        pos = positions.get(node.key)
        if pos is None:
            return
        x, y = pos
        node_radius = 20
        ellipse = QGraphicsEllipseItem(x - node_radius, y - node_radius, node_radius * 2, node_radius * 2)
        
        highlight_node = highlight_info.get("highlight_node")
        highlight_key = highlight_info.get("highlight_key") # 兼容BST查找
        
        if (highlight_node and node.key == highlight_node.key) or (highlight_key and node.key == highlight_key):
            pen = QPen(QColor("red"), 3)
            ellipse.setPen(pen)
        
        ellipse.setBrush(QBrush(QColor("#fdc500")))
        self.scene.addItem(ellipse)

        text = QGraphicsTextItem(str(node.key))
        text.setFont(QFont("Arial", 12))
        # BST 节点文本使用深紫色
        text.setDefaultTextColor(QColor("#4B0082"))
        text_x = x - text.boundingRect().width() / 2
        text_y = y - text.boundingRect().height() / 2
        text.setPos(text_x, text_y)
        self.scene.addItem(text)

        # 如果请求显示平衡信息，在节点上方显示 BF
        try:
            if hasattr(node, 'height') and highlight_info.get("balance_info"):
                balance = self._get_node_balance(node)
                balance_text = QGraphicsTextItem(f"BF:{balance}")
                balance_text.setFont(QFont("Arial", 8))
                balance_text.setDefaultTextColor(Qt.darkGray)
                balance_x = x - balance_text.boundingRect().width() / 2
                balance_y = y - node_radius - balance_text.boundingRect().height()
                balance_text.setPos(balance_x, balance_y)
                self.scene.addItem(balance_text)
        except Exception:
            # 保持稳健，如果节点没有 height 属性则不显示
            pass

        # 仅当子节点也在 positions 中时才递归绘制，防止画出未被包含在当前布局中的节点
        if node.left and positions.get(node.left.key) is not None:
            self._draw_bst_nodes(node.left, positions, highlight_info)
        if node.right and positions.get(node.right.key) is not None:
            self._draw_bst_nodes(node.right, positions, highlight_info)

    def display_info_text(self, text: str, color=QColor("black"), origin: str = None):
        """
        在画布左上角显示一段信息文本
        """
        try:
            self._cached_info_text = (text, color)
        except Exception:
            self._cached_info_text = None

        try:
            self.draw_right_text_box(text, color)
            try:
                if origin:
                    self._cached_right_box_origin = origin
                else:
                    self._cached_right_box_origin = None
            except Exception:
                pass
        except Exception:
            try:
                info_item = QGraphicsTextItem(text)
                info_item.setFont(QFont("Arial", 12, QFont.Bold))
                info_item.setDefaultTextColor(color)
                info_item.setPos(2, 2)
                self.scene.addItem(info_item)
                self._cached_info_item = info_item
            except Exception:
                pass

    def draw_right_text_box(self, text: str, color=QColor("black"), max_width: int = 300):
        """
        在画布右侧绘制一个带背景的文本框，用于显示构建/演示说明，避免遮挡树的根节点。
        会尝试移除之前绘制的右侧文本框以防重叠
        """
        try:
            # 尝试移除之前缓存的右侧文本框
            if hasattr(self, '_cached_right_box') and self._cached_right_box is not None:
                try:
                    rect_item, text_item = self._cached_right_box
                    self.scene.removeItem(rect_item)
                    self.scene.removeItem(text_item)
                except Exception:
                    pass
                self._cached_right_box = None
        except Exception:
            pass

        # 创建文本项，限制宽度以自动换行
        info_item = QGraphicsTextItem(text)
        info_item.setFont(QFont("Arial", 12))
        info_item.setDefaultTextColor(color)
        try:
            info_item.setTextWidth(max_width)
        except Exception:
            pass

        # 计算文本边界并创建一个矩形背景
        bbox = info_item.boundingRect()
        padding = 10
        box_w = bbox.width() + padding * 2
        box_h = bbox.height() + padding * 2

        try:
            viewport_rect = self.canvas.viewport().rect()
            top_right_view = viewport_rect.topRight()
            top_right_scene_point = self.canvas.mapToScene(top_right_view)
            box_x = top_right_scene_point.x() - box_w - 20
            box_y = top_right_scene_point.y() + 10
        except Exception:
            try:
                view_w = int(self.canvas.width()) if hasattr(self, 'canvas') else 800
            except Exception:
                view_w = 800
            box_x = max(20, view_w - box_w - 20)
            box_y = 20

        rect_item = QGraphicsRectItem(box_x, box_y, box_w, box_h)
        rect_item.setBrush(QBrush(QColor("#f5f5f5")))
        rect_item.setPen(QPen(QColor("#cccccc"), 1))
        self.scene.addItem(rect_item)

        # 将文本放在矩形内并添加
        info_item.setPos(box_x + padding, box_y + padding)
        self.scene.addItem(info_item)

        # 缓存对 scene 中右侧文本框的引用，以便下次移除/替换
        try:
            self._cached_right_box = (rect_item, info_item)
        except Exception:
            self._cached_right_box = None

    def _auto_scale_view(self, padding: int = 40, min_scale: float = 0.2, max_scale: float = 1.0):
        """
        自动缩放窗口视图
        """
        try:
            try:
                excluded = set()
                if hasattr(self, '_cached_right_box') and self._cached_right_box:
                    try:
                        excluded.add(self._cached_right_box[0])
                        excluded.add(self._cached_right_box[1])
                    except Exception:
                        excluded = set()
                items = [it for it in self.scene.items() if it not in excluded]
                if not items:
                    rect = QRectF()
                else:
                    rect = items[0].sceneBoundingRect()
                    for it in items[1:]:
                        rect = rect.united(it.sceneBoundingRect())
            except Exception:
                rect = self.scene.itemsBoundingRect()

            if rect.isEmpty() or rect.width() == 0 or rect.height() == 0:
                try:
                    self.canvas.resetTransform()
                except Exception:
                    pass
                return

            view_w = max(1, self.canvas.viewport().width() - padding)
            view_h = max(1, self.canvas.viewport().height() - padding)

            scale_x = view_w / rect.width()
            scale_y = view_h / rect.height()
            scale = min(scale_x, scale_y, max_scale)
            if scale <= 0:
                scale = min_scale

            try:
                viewport_center = self.canvas.viewport().rect().center()
                center_scene = self.canvas.mapToScene(viewport_center)
            except Exception:
                center_scene = None

            try:
                self.canvas.resetTransform()
                self.canvas.scale(scale, scale)

                if center_scene is not None:
                    try:
                        self.canvas.centerOn(center_scene)
                    except Exception:
                        pass
            except Exception:
                pass
        except Exception:
            pass

    def reset_view_transform(self):
        """
        重置视图变换并将视图中心对准场景内容中心（如果有内容），
        否则对准场景原点
        """
        try:
            self.canvas.resetTransform()
            rect = self.scene.itemsBoundingRect()
            if rect.isEmpty():
                try:
                    self.canvas.centerOn(0, 0)
                except Exception:
                    pass
            else:
                try:
                    self.canvas.centerOn(rect.center())
                except Exception:
                    pass
        except Exception:
            pass

    def reset_view_for_load(self):
        """
        在加载新内容后重置视图，清除任何缓存的滚动位置或缩放状态
        以确保新内容从默认视图状态开始显示
        """
        try:
            self.canvas.resetTransform()
        except Exception:
            pass
        
        try:
            self.scene.setSceneRect(self.scene.itemsBoundingRect())
        except Exception:
            pass

    def center_on_scene_content(self):
        """
        将视图中心对准场景内容的中心（排除右侧缓存文本框）
        """
        try:
            try:
                self._auto_scale_view()
            except Exception:
                pass

            excluded = set()
            if hasattr(self, '_cached_right_box') and self._cached_right_box:
                try:
                    excluded.add(self._cached_right_box[0])
                    excluded.add(self._cached_right_box[1])
                except Exception:
                    excluded = set()
            items = [it for it in self.scene.items() if it not in excluded]
            if not items:
                return
            rect = items[0].sceneBoundingRect()
            for it in items[1:]:
                rect = rect.united(it.sceneBoundingRect())
            try:
                self.canvas.centerOn(rect.center())
            except Exception:
                pass
        except Exception:
            pass

    def _get_node_balance(self, node):
        """获取AVL树节点的平衡因子"""
        if not node:
            return 0
        left_height = node.left.height if node.left else 0
        right_height = node.right.height if node.right else 0
        return left_height - right_height

    def _draw_bst_edges(self, node, positions, use_id=False):
        """
        递归绘制连线
        根据计算好的坐标，绘制从父节点到子节点的线条
        """
        if not node:
            return
        start_key = id(node) if use_id else node.key
        start_pos = positions.get(start_key)

        # 只有当当前节点在 positions 中时才绘制和递归其边
        if not start_pos:
            return

        if node.left:
            end_key = id(node.left) if use_id else node.left.key
            end_pos = positions.get(end_key)
            if end_pos:
                line = QGraphicsLineItem(start_pos[0], start_pos[1], end_pos[0], end_pos[1])
                # 使用浅蓝色的线条来表示树的连接
                edge_pen = QPen(QColor("#ADD8E6"), 2)
                line.setPen(edge_pen)
                self.scene.addItem(line)
                # 仅在子节点有位置的情况下递归绘制子边
                self._draw_bst_edges(node.left, positions, use_id)

        if node.right:
            end_key = id(node.right) if use_id else node.right.key
            end_pos = positions.get(end_key)
            if end_pos:
                line = QGraphicsLineItem(start_pos[0], start_pos[1], end_pos[0], end_pos[1])
                # 使用浅蓝色的线条来表示树的连接
                edge_pen = QPen(QColor("#ADD8E6"), 2)
                line.setPen(edge_pen)
                self.scene.addItem(line)
                self._draw_bst_edges(node.right, positions, use_id)
