/*==================================================================
 * 编译原理实验二：语法分析程序
 * part2funcs.c - 辅助函数：语法树构建、遍历、释放，以及主函数
 *==================================================================*/
#include "part2.h"
#include <time.h>

FILE *fin = NULL;   /* 输入文件 */
FILE *fout = NULL;  /* 输出文件 */

/*--------------------------------------------------------------
 * print2file - 同时输出到屏幕和文件
 *--------------------------------------------------------------*/
void print2file(char *s) {
    printf("%s", s);
    if (fout) fprintf(fout, "%s", s);
}

/*--------------------------------------------------------------
 * yyerror - 错误处理函数
 *--------------------------------------------------------------*/
void yyerror(const char *s) {
    fprintf(stderr, "语法错误: %s\n", s);
}

/*--------------------------------------------------------------
 * newnode - 创建一个内部节点
 * len:       孩子节点个数
 * name:      节点名称
 * brothers:  孩子节点的指针数组
 *
 * 将 brothers[0] 作为第一个孩子，其余兄弟依次链接
 *--------------------------------------------------------------*/
struct node *newnode(int len, char *name, struct node *brothers[]) {
    struct node *new = (struct node *)malloc(sizeof(struct node));
    if (!new) {
        fprintf(stderr, "内存分配失败！\n");
        exit(1);
    }
    new->name = name;
    new->child = brothers[0];           /* 第一个孩子 */
    /* 将兄弟节点串联起来 */
    for (int i = 0; i < len - 1; i++) {
        brothers[i]->brother = brothers[i + 1];
    }
    /* 最后一个兄弟的 brother 为 NULL（由 newleaf 已设置） */
    new->brother = NULL;
    return new;
}

/*--------------------------------------------------------------
 * newleaf - 创建一个叶子节点（终端节点）
 * name: 叶子节点的名称
 *--------------------------------------------------------------*/
struct node *newleaf(char *name) {
    struct node *t = (struct node *)malloc(sizeof(struct node));
    if (!t) {
        fprintf(stderr, "内存分配失败！\n");
        exit(1);
    }
    t->name = name;
    t->brother = NULL;
    t->child = NULL;
    return t;
}

/*--------------------------------------------------------------
 * traverse - 前序遍历语法树，带缩进输出
 * depth: 当前深度（每级缩进2个"--"）
 * root:  当前遍历的根节点
 *
 * 输出格式示例：
 *   P
 *   --L
 *   ----S
 *   ------ID
 *--------------------------------------------------------------*/
void traverse(int depth, struct node *root) {
    /* 打印缩进 */
    for (int i = 0; i < depth; i++) {
        print2file("-");
    }
    /* 打印节点名称 */
    print2file(root->name);
    print2file("\n");

    /* 递归遍历孩子节点（深度+2） */
    if (root->child != NULL) {
        traverse(depth + 2, root->child);
    }
    /* 递归遍历兄弟节点（深度不变） */
    if (root->brother != NULL) {
        traverse(depth, root->brother);
    }
}

/*--------------------------------------------------------------
 * treefree - 递归释放语法树的内存
 * root: 要释放的树的根节点
 *--------------------------------------------------------------*/
void treefree(struct node *root) {
    /* 先处理叶子孩子节点（没有更深节点时直接释放） */
    if (root->child != NULL
        && root->child->child == NULL
        && root->child->brother == NULL) {
        free(root->child);
        root->child = NULL;
    }
    /* 先处理叶子兄弟节点 */
    if (root->brother != NULL
        && root->brother->child == NULL
        && root->brother->brother == NULL) {
        free(root->brother);
        root->brother = NULL;
    }
    /* 递归释放子树 */
    if (root->child != NULL) {
        treefree(root->child);
    }
    if (root->brother != NULL) {
        treefree(root->brother);
    }
}

/*--------------------------------------------------------------
 * main - 主函数
 * 1. 读取并显示输入文件内容
 * 2. 调用 yyparse() 进行语法分析
 * 3. 显示输出文件内容
 *--------------------------------------------------------------*/
int main(int argc, char *argv[]) {
    const char *infile = (argc > 1) ? argv[1] : "input.txt";
    const char *outfile = (argc > 2) ? argv[2] : "output.txt";

    /* ---- 步骤1: 先读取并展示输入源代码 ---- */
    printf("========================================\n");
    printf("  编译原理实验二：语法分析程序\n");
    printf("========================================\n\n");

    /* 获取当前时间戳，证明是实时生成的 */
    time_t now = time(NULL);
    printf("[生成时间] %s\n", ctime(&now));

    printf("[输入文件] %s\n", infile);
    printf("[输出文件] %s\n\n", outfile);

    printf("--- 输入的源代码 ---\n");
    {
        FILE *preview = fopen(infile, "r");
        if (preview) {
            char line[512];
            int cnt = 0;
            while (fgets(line, sizeof(line), preview)) {
                printf("  %s", line);
                cnt++;
            }
            fclose(preview);
            if (cnt == 0) {
                printf("  (文件为空)\n");
            }
        } else {
            printf("  (无法打开文件)\n");
        }
    }
    printf("--- 源代码结束 ---\n\n");

    /* ---- 步骤2: 重新打开文件进行语法分析 ---- */
    fin = fopen(infile, "r");
    if (!fin) {
        fprintf(stderr, "错误：无法打开输入文件 \"%s\"\n", infile);
        system("pause");
        return 1;
    }

    fout = fopen(outfile, "w");
    if (!fout) {
        fprintf(stderr, "错误：无法打开输出文件 \"%s\"\n", outfile);
        fclose(fin);
        system("pause");
        return 1;
    }

    extern FILE *yyin;
    yyin = fin;

    printf("--- 实时生成的语法分析树 ---\n");

    /* 执行语法分析 */
    int result = yyparse();

    printf("--- 语法分析树结束 ---\n\n");
    if (result == 0) {
        printf("[状态] 语法分析成功完成！\n");
    } else {
        printf("[状态] 语法分析完成，但存在错误。\n");
    }

    fclose(fin);
    fclose(fout);

    /* ---- 步骤3: 展示输出文件内容 ---- */
    printf("\n[输出文件 %s 完整内容]\n", outfile);
    printf("----------------------------------------\n");
    {
        FILE *show = fopen(outfile, "r");
        if (show) {
            char line[256];
            while (fgets(line, sizeof(line), show)) {
                printf("%s", line);
            }
            fclose(show);
        }
    }
    printf("----------------------------------------\n");

    printf("\n提示: 修改 %s 后重新双击 tree.exe 即可看到新结果。\n\n", infile);
    printf("按任意键退出...\n");
    system("pause");
    return result;
}
