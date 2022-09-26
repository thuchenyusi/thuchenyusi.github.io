---
layout: post
title:  "C语言：宏"
author: 卡夫卡的K
date:   2022-09-22 00:47:35 +0800
categories: learn clang
tags: [C语言, 编程]
---

C语言中，宏几乎随处可见，宏将标识符转换成相应的代码段，能够起到复用代码，防止霰弹式样修改的作业用。

但宏也是危险的，宏由预处理器进行处理，从而导致编译器和程序员所看见的代码存在区别，这种不直观性往往是各类bug的根源，许多代码规范都强调了宏的危险性。

尽管如此，宏的许多特性，如串化（stringifying）、连接（concatenation）等在C语言中的作用却是无可替代的。作为C程序员只有理解了宏的作用机制，真正了解代码中各类宏的含义，才能正确的使用宏。

## 使用宏

宏的常见作用是减少代码的重复，一般用于定义各类常量和简单的类函数的代码段。通过#define *identifer* *replacement-list*，即可使用*identifer*来代替*replacement-list*，#define在所在行的前面只能有空白字符。如以下代码：

```c
#define BUFFER_SIZE 1024
foo = (char *) malloc (BUFFER_SIZE);

#define NUMBERS 1, \
                2, \
                3
int x[] = { NUMBERS };

#define lang_init()  c_init()
lang_init()

#define min(X, Y)  ((X) < (Y) ? (X) : (Y))
x = min(a, b); 
```

经过预处理器处理后，其等价于：

```c
foo = (char *) malloc (1024);

int x[] = { 1, 2, 3 };

c_init()

x = ((a) < (b) ? (a) : (b)); 
```

## 宏的处理

### 处理时机

首先必须明白，宏的核心作用是给代码段以名字，然后用代码段去替代后续代码中名字出现的地方。因此宏的实质就是文本替换，其操作由预处理器执行，从C标准的角度，是于翻译阶段（translation phase）4进行处理。

除了C、C++和Object-C外，C预处理器也可被用于其他文本的处理，尤其过去C预处理器经常被滥用做通用的文本预处理系统。但这样的作法是存在风险的，如将C预处理器用于Makefile，C预处理将会移除tab字符，导致Makefile失效。在现代不应该采用这种做法，即使所用的语言没有相应功能，也应该采用通用的文本处理系统如m4。

预处理器会在初始处理阶段先处理三联符、行尾的反斜线和注释，这也是C标准中所定义的翻译阶段1、2、3所做的操作的一部分。


因此，宏因为过长或可读性而需要换行时，可以用在行尾使用反斜线\，预处理器会将其转换为空格符。

```c
#define NUMBERS 1, \
                2, \
                3
int x[] = { NUMBERS };
// is equivalent to
int x[] = { 1, 2, 3 };
```

预处理器会将注释转换为空格符，因此以下的定义是合法但不推荐的：

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

此后还会进行记号化（tokenization），将文件内容分解成不同类型的记号。

编译器的作用时间在预处理器之后，因此编译错误都是在宏展开后再进行检测的，预处理阶段只能处理很少的错误。

## 宏指令的语法

宏指令有如下的5种语法，前4种是定义宏，最后1种是取消定义，其中第3、4种的变长参数列表宏为C99标准中引入。

```c
#define identifier replacement-list(optional)
#define identifier( parameters ) replacement-list
#define identifier( parameters, ... ) replacement-list
#define identifier( ... ) replacement-list
#undef identifier
```

根据宏的实际作用，可以把宏分为两类：类对象的宏和类函数的宏。

## 类对象的宏（Object-like Macros）

类对象的宏，简单的将标识符替换为替换列表，如下所示。

```c
#define BUFFER_SIZE 1024
foo = (char *) malloc (BUFFER_SIZE);

#define NUMBERS 1, \
                2, \
                3
int x[] = { NUMBERS };

#define DEBUG
```

再次注意只是简单的将标识符替换为替换列表，因此不要添加多余的符号，如不要写成如下形式：

```c
#define BUFFER_SIZE = 1024
// becomes malloc (= 1-24)
foo = (char *) malloc (BUFFER_SIZE);

#define N 100;
// becomes int a[100;];
int a [N];
```
### 给常量命名

类对象的宏最常见的用途就是用于给常量命名，这类常量被K&R称作明示常量（manifest constant），如下所示：

```c
#define STE_LEN 80
#define MEME_ERR "Error: not enough memory"
```

使用宏给常量命名有如下优点：

- 通过给常量取易于理解的名字使程序更易读。
- 对于会多处使用的常量，通过宏统一定义可是使程序更易于修改。
- 可以有效减少typo导致的错误。

当然，考虑到后续所说的种种陷阱，如果不选用宏（如采用常变量）也能起到相应作用时，并不建议采用宏。

### 控制条件编译

宏也可用于控制条件编译，此时可以不需要后面的替换列表。

```c
#define DEBUG

#ifdef DEBUG
// some code
#endif
```

有关条件编译的内容，本文不多赘述。

## 类函数的宏（Function-like Macros）

类函数的宏后面跟着括号，括号内中可以有可选的参数列表。

类函数的宏可以不带参数。

```c
#define lang_init()  c_init()

lang_init();
// is equivalent to
c_init();
```

参数列表也可不为空，如下所示：

```c
min(X, Y)  ((X) < (Y) ? (X) : (Y))

x = min(a, b);
y = min(1, 2);
z = min(a + 28, *p);
// is equivalent to
x = ((a) < (b) ? (a) : (b));
y = ((1) < (2) ? (1) : (2));
z = ((a + 28) < (*p) ? (a + 28) : (*p));
```

注意虽然使用类函数宏时没有要求，但定义类函数宏时括号必须紧跟着宏名，不然会被识别成类对象宏，如下所示：
```c
#define lang_init ()  c_init()

lang_init();
// is equivalent to
()  c_init()();
```

{% include warning.html 
    content="注意，字符串字面值中的参数不会被替换，考虑到记号化是在处理宏指令完成的，这并不令人感到意外。" %}

如下所示：
```c
#define foo(x) x, "x"

foo(bar);
// is equivalent to
bar, "x"
```
### 串化（Stringizing）

预处理操作符#用于将宏转变为字符串，这也被叫做串化。

如下所示：

```c
#define PRINT_INT(n) printf(#n " = %d\n", n)

PRINT_INF(i/j);
// is equivalent to
printf("i/j" " = %d\n", i/j);
// is equivalent to
printf("i/j = %d\n", i/j);
```
{% include warning.html 
    content="注意，当宏参数用于串化时，不会先进行宏展开，仅仅使用一遍串化是不能将宏的结果串化的。" %}

如下所示，如果想使宏的结果串化，需要使用2级宏：

```c
#define xstr(s) str(s)
#define str(s) #s
#define foo 4

str (foo);
// is equivalent to
"foo"

xstr (foo)
// is equivalent to
str (4)
// is equivalent to
"4"
```

### 变长参数列表

同样在C99标准，还引入了变长参数列表，如下所示：

```c
#define eprintf(...) fprintf (stderr, __VA_ARGS__)

eprintf ("%s:%d: ", input_file, lineno);
// is equivalent to
fprintf (stderr, "%s:%d: ", input_file, lineno);
```

如下也是可以的：
```c
#define eprintf(format, ...) fprintf (stderr, format, __VA_ARGS__)

eprintf ("%s:%d: ", input_file, lineno);
// is equivalent to
fprintf (stderr, "%s:%d: ", input_file, lineno);
```

### 空的宏参数
在C99标准后，还支持空的宏参数，但对应的逗号不能省略（在C++20标准后允许省略，部分编译器也有自己的扩展，具体建议参见所用编译器的说明），如下所示：

```c
#define ADD(x,y) (x+y)

i = ADD(j, k);
c = ADD( ,b);

// is equivalent to
i = (j+k);
c = (+b);
```
