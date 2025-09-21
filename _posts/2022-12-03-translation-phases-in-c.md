---
layout: post
title:  C语言的翻译阶段
author: me
date:   2022-12-03 17:10:44 +0800
categories: learn clang
tags: [C, C++]
---

> 本文基于C17(C18)版本。
{: .prompt-info }

一个C语言程序不需要全部在同一时间翻译。程序的文本被保存在称为源文件（或预处理文件）的单元中。一个源文件连同所有头文件和通过预处理指令#include包含的源文件被称为预处理的翻译单元。在预处理之后，一个预处理翻译单元被称为翻译单元。

以前翻译过的翻译单元可以单独保存，也可以保存在库中。一个程序的独立翻译单元通过（例如）调用其标识符有外部链接的函数、操作其标识符有外部链接的对象或操作数据文件进行交流。翻译单元可以单独翻译，然后再链接成一个可执行程序。

翻译过程被分为以下8个翻译阶段（translation phases）。

> 和C++相比，最大的区别就是少了和模板相关的阶段，缺乏模板也正是C语言相对C++编译期计算能力孱弱的核心原因。
{: .prompt-info }

## 阶段1

### 字符映射

这是阶段1的最主要的工作，将物理源文件多字节字符转换为源字符集（source character set）。具体转换方式由实现定义。

该步骤一个很重要的工作就是将行尾（end-of-line indicators，如Linux: \n、MacOS: \r、Windows: \n\r），替换为NL字符（new-line character)。

### 三联符处理

由于某些老式键盘不支持基本源字符中的部分字符吗，标准中引入了以??开头的三联符（trigraph）来代替相应字符，三联符的替换也是在本阶段进行。如下表所示：

| 三联符 | 标点字符 |
| ------ | -------- |
| ??=    | #        |
| ??(    | \[       |
| ??/    | \\       |
| ??)    | \]       |
| ??'    | ^        |
| ??<    | \{       |
| ??!    | \|       |
| ??>    | \}       |
| ??-    | ~        |

这样的代替方式使得许多代码难以理解。如下所示，使用三联符会使打印更难理解：

```c
// 开启三联符时，将打印What|
printf( "What??!\n" );
// 需要转义第2个?，才打印为What??!
printf( "What?\?!\n" );
```

更有甚者，会对程序运行逻辑产生误判，如下所示，??/被转换成\会使得return 0被注释：

```c
int trigraphsavailable() // returns 0 or 1; language standard C99 or later
{
 // are trigraphs available??/
 return 0;
#return 1;
}
```

正因如此，很多现代编译器实现默认不会处理三联符，如需处理，则要显示打开（如gcc -trigraphs）。相对的，不容易引起歧义的双联符得到了保留（不过双联符不在本阶段进行处理）。

| 双联符 | 标点字符 |
| **** | **** |
| <: | [ |
| :> | ] |
| <% | { |
| %> | } |
| %: | # |
| %:%: | ## |

> C++17标准已经废弃三联符，而根据草案，C23中也预计将废弃三联符的处理。
{: .prompt-warning }

## 阶段2

### 行合并

阶段2中，将以\结束的行和下一行合并。实现从物理源文件行到逻辑源文件行的转换。如下所示:

```c
#define NUMBERS 1, \
                2, \
                3
int x[] = { NUMBERS };
// is equivalent to
int x[] = { 1, 2, 3 };
```

## 阶段3

### 记号化

此阶段中，源文件被分解成预处理记号和空白字符（包括注释）。

预处理记号在标准中分为如下几类：

1. header-name。头文件名。
2. identifier。标识符，以数字、字母、下划线构成，而且开头只能为字母或下划线的字符序列。
3. pp-number。数字，如1、1.11、1.2E10等等。
4. character-constant。字符常量，如'c'。
5. string-literal。字符串常量，如"string"、u8"String"等。
6. punctuator。标点字符，如\[、\]、++、->、?以及之前提到的双联符等等。

其他非空字符也被当做预处理记号。

每个记号被分解时也会参考上下文，并不仅仅依赖本身的组成，如对#include的处理。

### 注释转换为空格字符

在此阶段中，注释会被转换为空格字符。结合本阶段的两点，可以写出如下合法（但极度不推荐）的代码：

```c
/\
*
*/ # /*
*/ defi\
ne FO\
O 10\
20

// is equivalent to
#define FOO 1020
```

## 阶段4

### 预处理指令、宏展开和_Progma

执行预处理指令、宏展开和_Progma一元运算符。

比较常见的有：

1. #include指令下进行头文件的包含。
2. #define指令与#、##下的宏的展开，相关内容比较复杂，本文不详细叙述。
3. #if、#ifdef等指令下的条件编译。
4. #progma指令（或等价的_Progma一元运算符），最常见的有#progma once，该指令和编译器高度相关，许多行为都取决于实现，本文也不详细叙述。

此外还有#error和#line等指令。

1. #error通常和#if等条件包含指令一同使用，用于在预处理期检测错误。
2. #line则是在文件存在复杂包含关系时会使用，和__LINE__联合使用方便定位错误。

如下cJSON中的示例，利用#error检测头文件版本和源文件版本是否一致。

```c
/* This is a safeguard to prevent copy-pasters from using incompatible C and header files */
#if (CJSON_VERSION_MAJOR != 1) || (CJSON_VERSION_MINOR != 7) || (CJSON_VERSION_PATCH != 14)
    #error cJSON.h and cJSON.c have different versions. Make sure that both have the same.
#endif
```

## 阶段5

### 字符集映射（含转义字符处理）

本阶段进行字符集映射（character-set mapping），从源字符集（source character set）转换为执行字符集（execution character set）。

最主要的工作是将\开头的转义字符转换为相应字符，如字符串中常见的\n、\t等控制字符都是在这个阶段进行转换。

转义的除了控制字符外，还有\"、\'、\\\\、\?等需要转义的标点字符，此外可以通过八进制和十六进制数进行转义，如\010（八进制）或\x008（十六进制）。如下所示，最长解析3个数字位：

```c
#define Bell '\07'

"\xabc"    /* one character  */
"\xab" "c" /* two characters */
```

此外还有通用字符的转义，具体可以参见文献[^escape]。

## 阶段6

### 相邻字符串合并

本阶段将中间只有空白字符的字符串合并成一个字符串，如下所示：

```c
"one"
"string"
// is equal to
"onestring"
```

需要注意，如果字符串前有前缀（如u），则需要保证相邻的所有字符串前缀一致。如下所示：

```c
u"hello" u"world"
// is equal to
u"helloworld"
```

## 阶段7

### 词法和语法分析

本阶段将预处理记号转换为记号，并对记号进行词法和语法分析（syntactically and semantically analyze），将其翻译为1个翻译单元。

本阶段可理解为通常所说的编译，过程比较复杂，本文不详细叙述。

## 阶段8

### 解析外部对象和函数

本阶段解析外部对象和函数，并将库组件链接至不在本翻译单元定义的对象和函数。

本阶段可理解为通常所说的链接，同样的，本文不详细叙述。

## 参考

* [Open Standards/C - Project status and milestones](https://www.open-std.org/jtc1/sc22/wg14/www/projects)
  
  可公开获取的C标准草案，也是本文主要参考源。

* [cppreference/翻译阶段](https://zh.cppreference.com/w/c/language/translation_phases)
  
  cppreference中关于C语言翻译阶段的描述。

* [GCC/The C Preprocessor](https://gcc.gnu.org/onlinedocs/cpp/index.html)
  
  GCC预处理器的相关说明。

* [Microsoft/C language documentation](https://learn.microsoft.com/en-us/cpp/c-language/)
  
  基于MSVC的C语言文档。

* [MERS BYU/standardC](https://www.mers.byu.edu/docs/standardC/)
  
  杨百翰大学有关C标准相关的文档，可供参考。

## 脚注

[^escape]: [cppreference/转义序列](https://zh.cppreference.com/w/c/language/translation_phases)
