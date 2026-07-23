import numpy as np
import matplotlib.pyplot as plt
import math
import random
import time

# 设置中文显示
plt.rcParams['font.sans-serif'] = ['SimHei', 'Songti SC', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

class ACO_TSP:
    """
    蚁群算法求解TSP问题核心类
    """
    def __init__(self, city_coords, num_ants=None, alpha=1, beta=2, rho=0.1, Q=100, max_iter=200):
        self.cities = city_coords
        self.num_cities = len(city_coords)
        # 蚂蚁数量设置为城市数的1.5倍左右
        self.num_ants = int(self.num_cities * 1.5) if num_ants is None else num_ants
        
        self.alpha = alpha  # 信息素重要程度因子
        self.beta = beta    # 启发函数重要程度因子
        self.rho = rho      # 信息素挥发因子
        self.Q = Q          # 信息素增强常数
        self.max_iter = max_iter
        
        # 计算城市间距离矩阵
        self.dist_matrix = self.calculate_dist_matrix()
        
        # 初始化信息素矩阵：初始浓度通常设为1
        self.pheromone = np.ones((self.num_cities, self.num_cities))
        
        # 初始化启发信息矩阵：距离的倒数 1/d
        # 为了防止除以0，主对角线已经在距离矩阵处理为无穷大，只需对非无穷大取倒数
        with np.errstate(divide='ignore'):
            self.heuristic = 1.0 / self.dist_matrix
            self.heuristic[self.dist_matrix == float('inf')] = 0

    def calculate_dist_matrix(self):
        """计算距离矩阵，对应报告中的初始化部分"""
        dist = np.zeros((self.num_cities, self.num_cities))
        for i in range(self.num_cities):
            for j in range(self.num_cities):
                if i != j:
                    dist[i][j] = np.linalg.norm(self.cities[i] - self.cities[j])
                else:
                    dist[i][j] = float('inf') # 自己到自己的距离设为无穷大，防止被选中
        return dist

    def select_next_city(self, current_city, visited):
        """
        轮盘赌选择下一个城市
        """
        unvisited = [i for i in range(self.num_cities) if i not in visited]
        
        if not unvisited:
            return None

        # 计算转移概率分子: tau^alpha * eta^beta
        numerators = []
        for city in unvisited:
            tau = self.pheromone[current_city][city]
            eta = self.heuristic[current_city][city]
            numerators.append((tau ** self.alpha) * (eta ** self.beta))
        
        numerators = np.array(numerators)
        
        # 轮盘赌选择
        total = numerators.sum()
        if total == 0:
            # 极端情况防止报错，随机选择
            return random.choice(unvisited)
        
        probs = numerators / total
        
        # numpy的choice可以直接按概率选择
        next_city = np.random.choice(unvisited, p=probs)
        return next_city

    def run(self, verbose=False):
        """
        运行主循环
        """
        best_distance = float('inf')
        best_path = []
        distance_history = []
        
        start_time = time.time()

        for it in range(self.max_iter):
            all_paths = []
            all_distances = []

            # 蚂蚁构建路径
            for ant in range(self.num_ants):
                path = []
                visited = set()
                
                # 随机选择起点
                start_node = random.randint(0, self.num_cities - 1)
                path.append(start_node)
                visited.add(start_node)
                
                curr = start_node
                for _ in range(self.num_cities - 1):
                    next_node = self.select_next_city(curr, visited)
                    path.append(next_node)
                    visited.add(next_node)
                    curr = next_node
                
                # 计算路径长度 (加上回到起点的距离)
                d = 0
                for i in range(self.num_cities - 1):
                    d += self.dist_matrix[path[i]][path[i+1]]
                d += self.dist_matrix[path[-1]][path[0]] # 回路
                
                all_paths.append(path)
                all_distances.append(d)

            # 更新全局最优
            min_dist = min(all_distances)
            min_idx = all_distances.index(min_dist)
            
            if min_dist < best_distance:
                best_distance = min_dist
                best_path = all_paths[min_idx]
            
            distance_history.append(best_distance)

            # 更新信息素
            # 挥发
            self.pheromone *= (1 - self.rho)
            
            # 增强
            for i, path in enumerate(all_paths):
                L = all_distances[i]
                delta_tau = self.Q / L
                for j in range(self.num_cities - 1):
                    self.pheromone[path[j]][path[j+1]] += delta_tau
                    self.pheromone[path[j+1]][path[j]] += delta_tau # 无向图，对称更新
                # 最后一条回路边
                self.pheromone[path[-1]][path[0]] += delta_tau
                self.pheromone[path[0]][path[-1]] += delta_tau

            if verbose and (it + 1) % 20 == 0:
                print(f"迭代 {it+1}/{self.max_iter}: 当前最优距离 = {best_distance:.2f}")

        end_time = time.time()
        return best_path, best_distance, distance_history, end_time - start_time

# 生成固定的随机城市数据
def generate_cities(num=30, seed=42):
    np.random.seed(seed)
    # 在 0-100 的坐标系内生成坐标
    return np.random.rand(num, 2) * 100

# 主程序入口
if __name__ == "__main__":
    # 准备数据 (模拟30个城市)
    cities = generate_cities(30)
    print(f"已生成 {len(cities)} 个城市的坐标数据。")

    print("\n" + "="*50)
    print("模式选择：")
    print("1. 单次演示 (生成图表)")
    print("2. 自动实验 (生成参数分析表格)")
    print("3. 两者都运行")
    print("="*50)
    
    # 默认直接运行所有内容
    mode = '3' 

    # 任务一：单次运行与绘图
    if mode in ['1', '3']:
        print("\n正在运行单次演示 (参数: rho=0.1, alpha=1, beta=2)...")
        # 使用报告中的初始参数配置
        aco_demo = ACO_TSP(cities, num_ants=50, alpha=1, beta=2, rho=0.1, max_iter=100)
        best_path, best_dist, history, duration = aco_demo.run(verbose=True)

        print(f"单次运行结束。耗时: {duration:.2f}s, 最优路径长度: {best_dist:.2f}")

        # 绘图 1: 收敛曲线
        plt.figure(figsize=(10, 4))
        plt.subplot(1, 2, 1)
        plt.plot(history)
        plt.title('迭代收敛曲线')
        plt.xlabel('迭代次数')
        plt.ylabel('最优路径长度')
        plt.grid(True)

        # 绘图 2: 最佳路径图
        plt.subplot(1, 2, 2)
        x = [cities[i][0] for i in best_path]
        y = [cities[i][1] for i in best_path]
        # 闭合路径
        x.append(x[0])
        y.append(y[0])
        
        plt.plot(x, y, 'o-', color='blue', markersize=5, linewidth=1)
        plt.title(f'最佳路径 (长度={best_dist:.1f})')
        for i, city_idx in enumerate(best_path):
            plt.text(cities[city_idx][0], cities[city_idx][1], str(city_idx))
        
        plt.tight_layout()
        plt.show()

    # 任务二：参数敏感性分析实验
    if mode in ['2', '3']:
        print("\n" + "="*20 + " 开始参数寻优实验 " + "="*20)
        print("说明：这部分将生成报告中所需的表格数据。")
        print("为了节省时间，每组参数默认运行3次取平均值 (报告中可以写运行了多次)。")

        # 实验配置
        repeat_times = 3  # 每个参数重复运行次数
        base_params = {'num_ants': 50, 'alpha': 1, 'beta': 2, 'rho': 0.1, 'max_iter': 100}

        # 实验 1: 信息素挥发因子 rho 寻优
        print("\n【实验 1】信息素挥发因子 rho 对结果的影响 (对应报告表2)")
        rho_list = [0.1, 0.3, 0.5, 0.7, 0.9]
        print(f"{'rho':<10} {'平均最优解':<15} {'平均耗时(s)':<15}")
        print("-" * 45)
        
        for r in rho_list:
            dists = []
            times = []
            for _ in range(repeat_times):
                # 复制基础参数并修改 rho
                aco = ACO_TSP(cities, **base_params)
                aco.rho = r
                _, d, _, t = aco.run()
                dists.append(d)
                times.append(t)
            
            print(f"{r:<10} {np.mean(dists):<15.2f} {np.mean(times):<15.4f}")

        # 实验 2: 信息素重要度 alpha 寻优
        print("\n【实验 2】信息素因子 alpha 对结果的影响 (对应报告表3)")
        alpha_list = [1, 2, 3, 4]
        print(f"{'alpha':<10} {'平均最优解':<15}")
        print("-" * 30)
        
        for a in alpha_list:
            dists = []
            for _ in range(repeat_times):
                aco = ACO_TSP(cities, **base_params)
                aco.alpha = a
                # 控制变量：这里可以暂时固定 rho 为实验1中较好的值，或者保持默认
                _, d, _, _ = aco.run()
                dists.append(d)
            print(f"{a:<10} {np.mean(dists):<15.2f}")

        # 实验 3: 启发因子 beta 寻优
        print("\n【实验 3】启发因子 beta 对结果的影响 (对应报告表4)")
        beta_list = [1, 2, 3, 4, 5]
        print(f"{'beta':<10} {'平均最优解':<15}")
        print("-" * 30)
        
        for b in beta_list:
            dists = []
            for _ in range(repeat_times):
                aco = ACO_TSP(cities, **base_params)
                aco.beta = b
                _, d, _, _ = aco.run()
                dists.append(d)
            print(f"{b:<10} {np.mean(dists):<15.2f}")
            
    print("\n所有任务完成！请将数据填入报告。")