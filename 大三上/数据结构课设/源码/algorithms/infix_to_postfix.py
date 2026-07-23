# algorithms/infix_to_postfix.py

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
    print("错误：无法从 'structures.stack' 导入 'SequentialStack' 类。")
    sys.exit(1)


def get_precedence(op):
    """
    返回运算符的优先级
    *, / : 2
    +, - : 1
    其他 : 0
    """
    if op in ('*', '/'):
        return 2
    elif op in ('+', '-'):
        return 1
    return 0


def is_operator(char):
    """判断字符是否为运算符"""
    return char in ('+', '-', '*', '/')


def infix_to_postfix_gen(expression):
    """
    中缀转后缀算法的生成器 (已支持多位数字/变量)
    """

    # 初始化
    stack = SequentialStack()
    postfix = []  # 用于存放后缀表达式结果（作为 token 列表）

    # 简单的预处理：去除空白符
    clean_expr = expression.replace(" ", "")
    # 全角转半角（适配中文括号）
    clean_expr = clean_expr.replace('（', '(').replace('）', ')')

    i = 0
    n = len(clean_expr)

    while i < n:
        char = clean_expr[i]

        # 识别多位操作数/变量
        if char.isalnum():
            start = i
            while i < n and clean_expr[i].isalnum():
                i += 1
            token = clean_expr[start:i]

            # 扫描到操作数
            yield {
                "token": token,
                "stack": stack.get_all_elements(),
                "postfix": list(postfix),
                "action_text": f"扫描到操作数: {token}",
                "step_type": "scan"
            }

            # 直接输出操作数
            postfix.append(token)
            yield {
                "token": token,
                "stack": stack.get_all_elements(),
                "postfix": list(postfix),
                "action_text": f"操作数 “{token}” -> 直接加入后缀表达式",
                "step_type": "output"
            }
            continue

        # 处理单字符符号（运算符或括号）
        token = char
        i += 1

        # 扫描到符号
        yield {
            "token": token,
            "stack": stack.get_all_elements(),
            "postfix": list(postfix),
            "action_text": f"扫描到字符: “{token}”",
            "step_type": "scan"
        }

        if token == '(':
            stack.push(token)
            yield {
                "token": token,
                "stack": stack.get_all_elements(),
                "postfix": list(postfix),
                "action_text": "左括号 “(” -> 压入栈中",
                "step_type": "push"
            }

        elif token == ')':
            while not stack.is_empty() and stack.top() != '(':
                top_op = stack.pop()
                postfix.append(top_op)
                yield {
                    "token": token,
                    "stack": stack.get_all_elements(),
                    "postfix": list(postfix),
                    "action_text": f"遇到 “)” -> 弹出栈顶 {top_op} 并输出",
                    "step_type": "pop"
                }

            if not stack.is_empty() and stack.top() == '(':
                stack.pop()
                yield {
                    "token": token,
                    "stack": stack.get_all_elements(),
                    "postfix": list(postfix),
                    "action_text": "匹配到 “(” -> 弹出丢弃",
                    "step_type": "pop_discard"
                }
            else:
                yield {
                    "token": token,
                    "stack": stack.get_all_elements(),
                    "postfix": list(postfix),
                    "action_text": "错误：括号不匹配！",
                    "step_type": "error"
                }

        elif is_operator(token):
            current_prec = get_precedence(token)
            while (not stack.is_empty() and
                   stack.top() != '(' and
                   get_precedence(stack.top()) >= current_prec):
                top_op = stack.pop()
                postfix.append(top_op)
                yield {
                    "token": token,
                    "stack": stack.get_all_elements(),
                    "postfix": list(postfix),
                    "action_text": f"栈顶 “{top_op}” 优先级 >= “{token}” -> 弹出并输出",
                    "step_type": "pop"
                }

            stack.push(token)
            yield {
                "token": token,
                "stack": stack.get_all_elements(),
                "postfix": list(postfix),
                "action_text": f"运算符 “{token}” -> 压入栈中",
                "step_type": "push"
            }

        else:
            yield {
                "token": token,
                "stack": stack.get_all_elements(),
                "postfix": list(postfix),
                "action_text": f"忽略未知字符: “{token}”",
                "step_type": "scan"
            }

    # 扫描结束，弹出栈中剩余运算符
    while not stack.is_empty():
        top_op = stack.pop()
        if top_op == '(':
            yield {
                "token": "END",
                "stack": stack.get_all_elements(),
                "postfix": list(postfix),
                "action_text": "错误：发现未匹配的 “(”",
                "step_type": "error"
            }
        else:
            postfix.append(top_op)
            yield {
                "token": "END",
                "stack": stack.get_all_elements(),
                "postfix": list(postfix),
                "action_text": f"表达式结束 -> 弹出剩余运算符 “{top_op}”",
                "step_type": "pop"
            }

    yield {
        "token": "DONE",
        "stack": stack.get_all_elements(),
        "postfix": list(postfix),
        "action_text": "转换完成！",
        "step_type": "done"
    }