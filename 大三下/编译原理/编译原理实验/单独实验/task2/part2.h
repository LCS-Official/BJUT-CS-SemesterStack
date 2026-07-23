/*==================================================================
 * 编译原理实验二：语法分析程序
 * part2.h - 头文件：定义语法树节点结构和函数声明
 *==================================================================*/
#ifndef PART2_H
#define PART2_H

#include <stdio.h>
#include <stdlib.h>

/* 文件指针：输入输出 */
extern FILE *fin;   /* 输入文件指针 */
extern FILE *fout;  /* 输出文件指针 */

/* 语法树节点结构 */
/* 采用"孩子-兄弟"表示法（二叉链表）存储多叉树 */
struct node {
    char *name;            /* 节点名称/标签 */
    struct node *child;    /* 指向第一个孩子节点 */
    struct node *brother;  /* 指向下一个兄弟节点 */
};

/* ---- 函数声明 ---- */

/* 打印字符串到屏幕和文件 */
void print2file(char *s);

/* 错误处理函数 */
void yyerror(const char *s);

/* 创建一个内部节点（有多个孩子的节点）
 * len: 孩子个数（即brothers数组长度）
 * name: 节点名称
 * brothers: 孩子节点指针数组
 */
struct node *newnode(int len, char *name, struct node *brothers[]);

/* 创建一个叶子节点（终端节点）
 * name: 叶子节点的名称/标签
 */
struct node *newleaf(char *name);

/* 遍历语法树并输出（前序遍历）
 * depth: 当前深度（用于缩进控制）
 * root: 当前遍历的根节点
 */
void traverse(int depth, struct node *root);

/* 释放语法树占用的内存
 * root: 要释放的树的根节点
 */
void treefree(struct node *root);

#endif /* PART2_H */
