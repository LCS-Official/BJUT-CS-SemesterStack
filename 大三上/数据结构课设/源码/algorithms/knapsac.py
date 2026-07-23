# ./algorithms/knapsac.py
import sys
import os
from typing import List, Tuple

# 导入 'SequentialStack'
try:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.append(parent_dir)
    
    # 从 'structures' 包中导入 'SequentialStack' 类
    from structures.stack import SequentialStack
except ImportError:
    print("错误：无法从 'structures.stack' 导入 'SequentialStack' 类。")
    print("请确保 'structures/stack.py' 文件存在，并且 'structures' 文件夹包含 '__init__.py' 文件。")
    sys.exit(1)


def solve_subset_sum_backtracking(weights: List[int], capacity: int) -> Tuple[int, List[int]]:
    """
    使用基于栈的回溯算法 (Stack-Based Backtracking) 解决子集和问题。
    """
    n = len(weights)
    if n == 0 or capacity <= 0:
        return 0, []

    stack = SequentialStack()  # 栈中存放的是物品的 *索引 (index)*
    current_capacity = capacity  # 剩余容量 T
    i = 0  # 当前正在考虑的物品索引

    # 简化版：只遍历所有物品一次，不进行回溯
    while i < n:
        current_weight = weights[i]
        
        # 如果当前物品能放入，就放入
        if current_weight <= current_capacity:
            stack.push(i)
            current_capacity -= current_weight
        
        # 继续看下一个物品
        i += 1

        # 如果背包被装满，返回解
        if current_capacity == 0:
            solution_indices = []
            while not stack.is_empty():
                solution_indices.append(stack.pop())
            solution_indices.reverse()
            
            solution_weights = [weights[idx] for idx in solution_indices]
            return capacity, solution_weights
    
    # 遍历完所有物品后，如果背包还没满，返回无解
    return 0, []


def solve_subset_sum_backtracking_gen(weights, capacity):
    """
    生成器版本：真正的回溯（DFS）算法，每一步 yield 事件来驱动可视化：
    {"action": "push"|"pop"|"found"|"no_solution", ...}
    """
    n = len(weights)
    if n == 0 or capacity <= 0:
        # 直接报无解（调用方会处理 None/空生成器情况）
        yield {"action": "no_solution"}
        return

    stack = SequentialStack()  # 存储索引

    # 递归回溯生成器
    def backtrack(start_index, current_rem):
        # 终止条件：正好填满
        if current_rem == 0:
            return True

        # 剪枝：容量透支
        if current_rem < 0:
            return False

        for i in range(start_index, n):
            w = weights[i]

            # 剪枝：当前物品过大则跳过
            if current_rem - w < 0:
                continue

            # 尝试放入
            stack.push(i)
            yield {
                "action": "push",
                "index": i,
                "weight": w,
                "remaining": current_rem - w,
                "stack": stack.get_all_elements().copy()
            }

            # 递归下一层（每个物品只能用一次）
            if (yield from backtrack(i + 1, current_rem - w)):
                return True

            # 回溯（弹出）
            stack.pop()
            yield {
                "action": "pop",
                "index": i,
                "remaining": current_rem,
                "stack": stack.get_all_elements().copy()
            }

        return False

    # 启动回溯
    if (yield from backtrack(0, capacity)):
        solution_indices = list(stack.get_all_elements())
        solution_weights = [weights[idx] for idx in solution_indices]
        yield {
            "action": "found",
            "indices": solution_indices,
            "weights": solution_weights,
            "total": capacity
        }
    else:
        yield {"action": "no_solution"}


if __name__ == '__main__':
    pass