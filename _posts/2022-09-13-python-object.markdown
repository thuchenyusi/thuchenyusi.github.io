---
layout: post
title:  "Python中的对象"
date: 2022-09-14 01:31:55 +0800
categories: study python
---

## 引言

对象是Python 中对数据的抽象。Python程序中的所有数据都是由对象或对象间关系来表示的。

Python中，一切皆对象。

## 对象的组成

在Python中，任何对象都有各自的标识号、类型和值。

### 标识号（identity）

一个对象被创建后，其标识号就**绝不会**改变。通过id()函数可以返回代表对象标识号的整数，is运算符可以用于判断两个对象标识号是否相同。

我们可以将对象的标识号理解为该对象在内存中的地址，实际上，在CPython中，id(x)就是存放x的内存的地址。

### 类型（type）

对象的类型决定该对象所支持的操作并且定义了该类型的对象可能的取值。type()函数能返回一个对象的类型 (类型本身也是对象)。

与标识号一样，一个对象的类型**通常是不可改变**的。

文档脚注中提到：

> 在某些情况下*有可能*基于可控的条件改变一个对象的类型。 但这通常不是个好主意，因为如果处理不当会导致一些非常怪异的行为。

#### Python是强类型的（strongly typed）

作为术语，强类型的和弱类型的的定义并不算精确，实际上编程语言中类型系统（type system）中的许多术语都有类似的问题，如类型安全（type safety），这些术语在不同场景其内涵可能有微妙的差别。也正因如此，在讨论语言的类型系统相关问题时，更应该注意其类型系统设计上的种种具体特性，而不能简单的以一句话结论带过。

Python被广泛认为是强类型的，其原因大概有如下几条：

1. Python的对象类型不会发生隐式转换。
2. Python会在运行中检测类型错误。

以上皆以Python的标准实现CPython为基准。实际上，很多编程语言特性是很难脱离了编译器/解释器对语言的具体实现来谈论的。

#### Python是动态类型的（dynamic typed）

Python也被广泛认为是动态类型的，其原因大概有如下几条：

1. Python的名称（(名称/标识符（name, aka. identifier）和对象)[名称/标识符（name, aka. identifier）和对象]）可以换绑不同类型的对象。
2. Python在运行时会进行动态类型检查。 

同样以Python的标准实现CPython为基准。

关于类型系统的相关讨论还能有更多，但正如上面所说，我们应该更注意其具体的特性，有关类型系统的其他内容放在词法分析、执行模型等部分分别来介绍可能会理解起来更为顺畅。

### 值（value）

有些对象的值可以改变。值可以改变的对象被称为可变对象；值不可以改变的对象就被称为不可变对象。

有关可变对象和不可变对象，我们会在下文做详细介绍。

### 名称/标识符（name, aka. identifier）和对象

以如下代码为例：

```python
a = 1
```

“a”即是名称（又可称为标识符），名称不是对象的组成部分，但名称可以指代对象。

名称通过绑定（binding）操作引入，方式可以有多种：

- 函数的正式参数，
- 类定义，
- 函数定义，
- 赋值表达式,
- 如果在一个赋值中出现，则为标识符的目标:
    - for循环头,
    - 在as后面的with语句，except子句或结构模式匹配中的as模式。
    - 在结构模式匹配中的捕获模式
- import语句。

对于从没有相应机制语言转过来的程序员，此概念可能较为难以理解。如在C语言中，类似`a = 1`的语句中，a作为变量其内存地址是确定的，再执行`a = 2`语句，则会对a对应的内存地址的值做更改，而在Python中，这只是将该名称绑定到另一个对象上，其对象所在的内存地址已经发生了改变。

## 可变性（immutable）

### 可变性的定义

Python中，对象可以依照可变性分为两类：可变对象和不可变对象。

在[官方文档](https://docs.python.org/3/glossary.html)中，可变性的定义如下：

> immutable
> 
> An object with a fixed value. Immutable objects include numbers, strings and tuples. Such an object cannot be altered. A new object has to be created if a different value has to be stored. They play an important role in places where a constant hash value is needed, for example as a key in a dictionary.


固定值是可变对象的最根本的属性，因此在Python的赋值语句中，如果左侧为不可变对象，则通常需要创建新的对象，再将名称和新对象绑定。

## 可哈希性（hashable）

### 可变性与可哈希性的关系

## 生命周期
