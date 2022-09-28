---
layout: post
title:  C语言：宏
author: me
date:   2022-09-22 00:47:35 +0800
categories: learn clang
tags: [C语言, 编程]
---

C语言中，宏几乎随处可见，宏将标识符转换成相应的代码段，能够起到复用代码，防止霰弹式样修改的作用。

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
lang_init();

#define min(X, Y)  ((X) < (Y) ? (X) : (Y))
x = min(a, b); 
```

经过预处理器处理后，其等价于：

```c
foo = (char *) malloc (1024);

int x[] = { 1, 2, 3 };

c_init();

x = ((a) < (b) ? (a) : (b)); 
```

## 宏的处理

### 处理时机

首先必须明白，宏的核心作用是给代码段以名字，然后用代码段去替代后续代码中名字出现的地方。因此宏的实质就是文本替换，其操作由预处理器执行，从C标准的角度，是于翻译阶段（translation phase）4进行处理。

目前预处理器通常和编译器等一同组成套件，一般编译器套件会提供预编译的处理结果，如GCC可以通过gcc -E选项输出预处理后的结果。

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

此后还会进行记号化（tokenization），将文件内容分解成不同类型的预处理记号。记号是以空格和分隔符（punctuators）分隔的，预处理器只会替换完整的记号，而不会替换记号的片段。

如下所示：
```c
#define SIZE 256

int BUFFER_SIZE;

if (BUFFER_SIZE > SIZE)
    puts("Error: SIZE exceeded");
// is equivalent to
if (BUFFER_SIZE > 256)
    puts("Error: SIZE exceeded");
```

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

类对象的宏，简单的将标识符展开为替换列表，如下所示。

```c
#define BUFFER_SIZE 1024
foo = (char *) malloc (BUFFER_SIZE);

#define NUMBERS 1, \
                2, \
                3
int x[] = { NUMBERS };

#define DEBUG
```

再次注意只是简单的将标识符展开为替换列表，因此不要添加多余的符号，如不要写成如下形式：

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

## 类函数的宏

类函数的宏（Function-like Macros）后面跟着括号，括号内中可以有可选的参数列表。

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

> 虽然使用类函数宏时没有要求，但定义类函数宏时括号必须紧跟着宏名，不然会被识别成类对象宏。
{: .prompt-warning }

如下所示：
```c
#define lang_init ()  c_init()

lang_init();
// is equivalent to
()  c_init()();
```

> 字符串字面值中的参数不会被展开，考虑到记号化是在处理宏指令完成的，这并不令人感到意外。
{: .prompt-warning }

如下所示：
```c
#define foo(x) x, "x"

foo(bar);
// is equivalent to
bar, "x";
```
### 串化

预处理操作符#用于将宏转变为字符串，这也被叫做串化（Stringizing）。

如下所示：

```c
#define PRINT_INT(n) printf(#n " = %d\n", n)

PRINT_INF(i/j);
// is equivalent to
printf("i/j" " = %d\n", i/j);
// is equivalent to
printf("i/j = %d\n", i/j);
```
> 和后续会提到的宏参数的展开规则不同，当宏参数用于串化时，不会先进行宏展开，仅仅使用一遍串化是不能将宏的结果串化的。
{: .prompt-warning }

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

## 宏的记号粘合

##运算符可以将两个记号粘合在一起，成为一个新的记号，，这被称作记号粘合（Token Concatenation）。

如下所示：

```c
#define MK_ID(n) i#n

int MK_ID(1), MK_ID(2), MK_ID(3);
// is equivalent to
int i1, i2, i3;
```

通过记号粘合，可以实现更为高级的代码复用，如结构体数组定义：
```c
struct command
{
  char *name;
  void (*function) (void);
};

#define COMMAND(NAME)  { #NAME, NAME ## _command }

struct command commands[] =
{
  COMMAND (quit),
  COMMAND (help),
};
// is equivalent to
struct command commands[] =
{
  { "quit", quit_command },
  { "help", help_command },
};
```

又或者是不同类型变量的通用算法：
```c
#define DeclareSort(prefix, type) \
static int \
_DeclareSort_ ## prefix ## _Compare(const void *a, const void *b) \
{ \
    const type *aa; const type *bb; \
    aa = a; bb = b; \
    if(aa < bb) return -1; \
    else if(bb < aa) return 1; \
    else return 0; \
} \
\
void \
prefix ## _sort(type *a, int n)\
{ \
    qsort(a, sizeof(type), n, _DeclareSort_ ## prefix ## _Compare); \
}

#include <stdlib.h>

/* note: must appear outside of any function, and has no trailing semicolon */
DeclareSort(int, int)

int
main(int argc, char **argv)
{
    int *a;
    int n;
    int_sort(a, n);
}
```

记号粘合可以将2个数字粘合为1个数字（如1.5），也可将多个字符粘合成1个多字符运算符（如+=）。

> 和串化类似，当宏参数用于记号粘合时，不会先进行宏展开。
{: .prompt-warning }
## 预定义宏

在C标准中，有一些预定义宏，每个宏表示一个整数常量或字符串字面量，用于提供当前编译或编译器本身的信息。这些预定义宏对于定位代码故障有着较大的帮助。

以下为C89标准中的预定义宏：
- __LINE__：编译文件中的行号。
- __FILE__：编译文件名。
- __DATE__：编译的日期（格式“Mmm dd yyyy”）。
- __TIME__：编译的时间（格式“hh:mm:ss”）。
- __STDC__：如果编译器符合C标准，那么值为1。

后续标准还支持了新的预定义宏，而编译套件本身可能也会提供自身扩展的预定义宏。具体可以参见相应的文档。

> C99标准中引入了__func__标识符，其作用与以上预定义宏类似，可以打印所在的函数名，通常和__LINE__与__FILE__一同使用，便于程序员进行调试。但其实际上并非预处理宏，也不由预处理器处理，其性质更接近于在函数体开头声明了存储了函数名的字符串静态变量。
{: .prompt-info }
## 宏的规则

### 宏的嵌套

宏的替换列表可以包含对其他宏的调用，预处理器在宏展开的过程中会重复检查替换列表，直到将所有宏均展开为止。

但是，宏是不能调用自身的。如下所示，首次展开后，预处理器不会再次将和宏同名的标识符展开，以阻止进入无限循环状态：

```c
#define foo (4 + foo)

foo;
// is equivalent to
(4 + foo)
```

与之类似，间接调用自身也是不被允许的。展开过程中遇到和宏同名的标识符后会停止展开，如下所示：

```c
#define x (4 + y)
#define y (2 * x)

x;
// is equivalent to
(4 + (2 * x));

y;
// is equivalent to
(2 * (4 + y));
```

### 宏的作用范围

和变量不同，宏的作用范围通常会从宏出现的位置到宏所在文件的结尾，即使宏定义在在函数内，宏的作用范围也会超出函数外。

### 除非完全相同，宏不可以被定义两遍

宏不可以被重复定义，除非两次定义除了间隔上的差异外（空白等均在宏指令执行前处理）应该完全一致，宏的替换列表和参数的记号也该完全一直。

### 宏可以通过#undef取消定义

定义了的宏可以通过#undef取消定义，从而减小其作用域。在#undef后，可以通过#define对宏进行再定义。

## 宏的实践

### 宏定义中的圆括号

在宏的替换列表中通常有大量圆括号，这都是为了避免宏展开时产生意想不到的结果，一般而言分为两类：

1. 整个替换列表应该在圆括号中。
2. 带参数的宏中，位于替换列表的参数名应该在圆括号中。

如下所示，对整个替换列表不加括号，其展开后的结果将变得极具误导性：

```c
#define TWO_PI 2*3.14159

conversion_factor = 360/TWO_PI;
// is equivalent to
conversion_factor = 360/2*3.14159;
```

对于带参数宏的参数同理，不加圆括号其展开后的结果极具误导性，如下所示：

```c
#define SCALE(x) (x*10)

j = SCALE(i+1);
// is equivalent to
j = SCALE(i+1*10);
```

可以看出，宏只是简单的文本替换操作，和真正的函数和对象其实质并不相同，因此必须通过括号来使其性质与对象和函数更为接近以减少误解。

### 宏定义中的逗号运算符

如果一个宏有多个表达式组成，一个解决方案是使用逗号运算符连接。

如下所示：
```c
#define ECHO(s) (get(s), put(s))

ECHO(str);
// is equivalent to
(get(str), put(str));
```

> 注意，不建议采用花括号和语句构成复合语句的方式定义宏，这类宏会在if语句等情况下产生误导性甚至是错误的结果。
{: .prompt-warning }

如下所示，else悬空导致语法错误，编译不能通过：

```c
#define ECHO(s) {get(s); put(s);}

if (echo_flag)
    ECHO(str);
else
    get(str);
// is equivalent to
if (echo_flag)
    {get(s); put(s);};
else
    get(str);

// is equivalent to
if (echo_flag) {
    get(s);
    put(s);
}; // if statement is over
else // error!
    get(str);
```

### 宏定义中的`do {...} while(0)`\

由于逗号运算符只能连接多个表达式，对于多语句的情况不能处理，通常采用`do {...} while(0)`的形式实现多语句的宏。当然多表达式的宏也可如此处理，这样处理也能避免宏在if等语句中展开时结果偏离预期。

如下所示：

```c
#define ECHO(s) \
            do { \
                get(s); \
                put(s); \
            } while(0)

ECHO(str);
// is equivalent to
do {
    get(s);
    put(s);
} while(0);
```

### foreach类型宏

另外一种常见的写法是将for语句或类似for语句的功能用宏来表示，如下所示：

```c
#define UpTo(i, n) for((i) = 0; (i) < (n); (i)++)

UpTo(i, n)
{
    ...
}
```

## 使用宏时的陷阱

上文已经提到，大多数宏类似与对象或函数，但是宏和对象与函数终究不同，宏仅仅只是编译前的文本替换操作。这种相似性和不同往往是很多误用宏的根源，下面举部分例子。

### 重复副作用

给带参数的类函数的宏传入带有副作用的表达式时，如果该参数使用多次，将会导致副作用也被重复多次。这与函数的行为并不相同。

如下所示，foo函数将被执行两次：
```c
#define min(X, Y)  ((X) < (Y) ? (X) : (Y))

next = min (x + y, foo (z));
// is equivalent to
next = ((x + y) < (foo (z)) ? (x + y) : (foo (z)));
```

可以改写成更安全的形式，如下X、Y参数仅使用了1次，规避了相应风险：
```c
#define min(X, Y)                \
({ typeof (X) x_ = (X);          \
   typeof (Y) y_ = (Y);          \
   (x_ < y_) ? x_ : y_; })
```

从编码实践上考虑，如果改写较为复杂或者其他原因不能改写时，建议在宏名字前加上UNSAFE之类前后缀，以提醒使用者。

```c
#define MIN_UNSAFE(X, Y)  ((X) < (Y) ? (X) : (Y))
```

### 宏参数的预扫描

在展开宏时，如果宏不被用于记号粘合或串化，预处理器会将宏参数中的宏预先扫面并展开，之后再被替换入替换列表中。紧接着，根据宏的嵌套展开规则，宏还会对替换后的替换列表再做宏展开。

对于绝大多数情况，即使宏参数只在替换前或替换后再做宏展开都不会对展开的结果有影响，但仍有几种情况例外。

如下所示，FUNC本身会先展开，此时就不会触发宏的自我引用：

```c
#define FUNC(x) (x + 1)

FUNC(FUNC(1));
// is equivalent to
((x + 1) + 1);
// without prescan it will be (FUNC(1) + 1)
```

如果宏的替换列表为没有被括号包括的逗号表达式，那么可能会引发错误，如下所示：

```c
#define foo  a,b
#define bar(x) lose(x)
#define lose(x) (1 + (x))

// bar(a,b), error!
bar(foo);
```

规避方法为再加一层括号，如下所示：

```c
#define foo  (a,b)
// or
#define bar(x) lose((x))
```

## 如何使用宏？

- 在使用宏前考虑其他的解决方案，如用常变量替代宏。
- 可以让宏和其他标识符有明显区别（如均大写），以避免错误使用。
- 对于不安全的宏，请尽量在宏名中指出，以提醒使用者。
- 对于过于复杂的宏，请添加注释，详细说明其含义和用法。
- 可以用#undef限制宏的作用域，以避免名字污染。
- 正确的给宏参数和替换列表加上括号和do{...} while(0)。
- 当其他方案不能奏效或过于繁琐，而使用宏确实能提高代码可读性或方便修改时，请大胆地使用吧！