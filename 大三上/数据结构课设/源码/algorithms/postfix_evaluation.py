# algorithms/postfix_evaluation.py

import sys
import os

# 导入 顺序栈 (保持与现有项目结构一致)
try:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.append(parent_dir)
    
    from structures.stack import SequentialStack
except ImportError:
    pass

def calculate(val1, val2, op):
    """辅助计算函数"""
    v1 = float(val1)
    v2 = float(val2)
    
    if op == '+': return v1 + v2
    if op == '-': return v1 - v2
    if op == '*': return v1 * v2
    if op == '/':
        if v2 == 0: return None # 除零错误处理
        return v1 / v2
    return 0

def postfix_evaluation_gen(expression):
    """
    后缀表达式求值生成器
    """
    stack = SequentialStack()
    
    # 简单的预处理
    tokens = expression.strip().split()
    
    if not tokens:
        yield {
            "token": "START",
            "stack": [],
            "action_text": "输入为空",
            "step_type": "error"
        }
        return

    for token in tokens:
        # 如果是数字
        if token.replace('.', '', 1).isdigit() or (token.startswith('-') and token[1:].replace('.', '', 1).isdigit()):
            stack.push(token)
            yield {
                "token": token,
                "stack": stack.get_all_elements(),
                "action_text": f"扫描到操作数 “{token}” -> 压入栈",
                "step_type": "push"
            }
        
        # 如果是运算符
        elif token in ('+', '-', '*', '/'):
            # 检查栈元素是否足够
            if stack.get_length() < 2:
                yield {
                    "token": token,
                    "stack": stack.get_all_elements(),
                    "action_text": f"错误：操作数不足，无法计算 “{token}”",
                    "step_type": "error"
                }
                return

            val2 = stack.pop() # 栈顶是右操作数
            val1 = stack.pop() # 次顶是左操作数
            
            # 产生一个中间状态（弹出两个数）
            yield {
                "token": token,
                "stack": stack.get_all_elements(),
                "action_text": f"遇到运算符 “{token}” -> 弹出 “{val2}” 和 “{val1}”",
                "step_type": "pop_calc_prepare",
                "calc_info": {"v1": val1, "v2": val2, "op": token}
            }

            res = calculate(val1, val2, token)
            
            if res is None:
                yield {
                    "token": token,
                    "stack": stack.get_all_elements(),
                    "action_text": "错误：除数不能为零",
                    "step_type": "error"
                }
                return
            
            # 格式化结果：如果是整数去尾，如果是小数则保留两位
            if res == int(res):
                res = int(res)
            else:
                res = round(res, 2)  # 保留两位小数
            
            stack.push(res)
            yield {
                "token": token,
                "stack": stack.get_all_elements(),
                "action_text": f"计算 “{val1} {token} {val2} = {res}” -> 压入栈",
                "step_type": "push_result"
            }
            
        else:
            yield {
                "token": token,
                "stack": stack.get_all_elements(),
                "action_text": f"忽略非法字符: “{token}”",
                "step_type": "ignore"
            }

    # 最终结果检查
    if stack.get_length() == 1:
        final_res = stack.top()
        yield {
            "token": "DONE",
            "stack": stack.get_all_elements(),
            "action_text": f"计算完成！最终结果: “{final_res}”",
            "step_type": "done",
            "result": final_res
        }
    else:
        yield {
            "token": "DONE",
            "stack": stack.get_all_elements(),
            "action_text": "错误：表达式无效（栈中剩余多个元素）",
            "step_type": "error"
        }