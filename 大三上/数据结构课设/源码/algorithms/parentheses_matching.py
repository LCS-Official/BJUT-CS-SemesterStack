# algorithms/parentheses_matching.py

import sys
import os

# 导入 顺序栈
try:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.append(parent_dir)
    
    from structures.stack import SequentialStack
except ImportError:
    pass

def parentheses_matching_gen(expression):
    """
    括号匹配算法生成器
    """
    stack = SequentialStack()
    # 定义匹配规则：右括号 -> 对应的左括号
    # 注意使用右括号作为键，映射到对应的左括号
    pairs = {')': '(', ']': '[', '}': '{', '）': '（'}
    
    # 预处理：移除空白符
    # 逐字符遍历原始字符串
    
    n = len(expression)
    
    yield {
        "index": -1,
        "char": "",
        "stack": [],
        "action_text": "准备开始检查...",
        "step_type": "start"
    }

    for i, char in enumerate(expression):
        # 1. 扫描字符
        yield {
            "index": i,
            "char": char,
            "stack": stack.get_all_elements(),
            "action_text": f"扫描到字符: “{char}”",
            "step_type": "scan"
        }

        # 2. 如果是左括号 -> 压栈
        if char in "([{（":
            stack.push(char)
            yield {
                "index": i,
                "char": char,
                "stack": stack.get_all_elements(),
                "action_text": f"遇到左括号 “{char}” -> 压入栈中",
                "step_type": "push"
            }
        
        # 3. 如果是右括号 -> 尝试匹配
        elif char in ")]}）":
            # 情况 A: 栈为空，无法匹配
            if stack.is_empty():
                yield {
                    "index": i,
                    "char": char,
                    "stack": [],
                    "action_text": f"错误：遇到右括号 “{char}” 但栈为空（缺少左括号）",
                    "step_type": "error"
                }
                return # 终止算法

            # 情况 B: 栈不为空，弹出栈顶
            top_char = stack.pop()
            yield {
                "index": i,
                "char": char,
                "stack": stack.get_all_elements(), # 此时已弹出
                "action_text": f"遇到右括号 “{char}” -> 弹出栈顶 “{top_char}” 进行比对",
                "step_type": "pop",
                "popped_char": top_char
            }

            # 检查是否匹配
            expected_left = pairs[char]
            if top_char != expected_left:
                yield {
                    "index": i,
                    "char": char,
                    "stack": stack.get_all_elements(),
                    "action_text": f"错误：括号不匹配！需要 “{expected_left}” 但弹出的是 “{top_char}”",
                    "step_type": "error_mismatch",
                    "mismatch_info": {"got": top_char, "expected": expected_left}
                }
                return # 终止算法
            else:
                yield {
                    "index": i,
                    "char": char,
                    "stack": stack.get_all_elements(),
                    "action_text": f"匹配成功： “{top_char}” 与 “{char}” 是一对",
                    "step_type": "match"
                }
        
        # 4. 其他字符 -> 忽略
        else:
            pass

    # 5. 循环结束，检查栈是否为空
    if stack.is_empty():
        yield {
            "index": n,
            "char": "END",
            "stack": [],
            "action_text": "检查结束：栈为空 -> 括号完全匹配！",
            "step_type": "done_success"
        }
    else:
        remaining = stack.get_all_elements()
        yield {
            "index": n,
            "char": "END",
            "stack": remaining,
            "action_text": f"错误：检查结束但栈不为空 -> 缺少右括号。剩余: {remaining}",
            "step_type": "error_unbalanced"
        }