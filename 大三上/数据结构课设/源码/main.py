# main.py
import sys
from PySide6.QtWidgets import QApplication
from views.main_window import MainWindow
from controllers.main_controller import MainController

def main():
    """主函数，应用程序的入口"""
    app = QApplication(sys.argv)
    
    # 1. 创建视图 (V)
    window = MainWindow()
    
    # 2. 创建控制器 (C), 并将视图的引用传递给它
    #    控制器将持有视图和模型的实例
    controller = MainController(view=window)
    
    # 3. 显示窗口
    window.show()
    
    # 启动应用的事件循环
    sys.exit(app.exec())

if __name__ == "__main__":
    main()