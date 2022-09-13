---
layout: post
title:  "Python中的对象"
date: 2022-09-14 01:31:55 +0800
categories: study python
---

# 引言

# 对象的组成

在Python中，任何对象都有各自的标识号、类型和值。

## 值（value）

## 类型（type）

## 标识（identity）

## is和==的区别

is用于判断标识是否相同，==用于判断值是否相同。

## 名称/标识符（name, aka. identifier）和对象

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
    - for 循环头,
    - 在 as 后面的 with 语句， except 子句或结构模式匹配中的 as 模式。
    - 在结构模式匹配中的捕获模式
- import 语句。

# 可变性（immutable）

## 可变性的定义

Python中，对象可以依照可变性分为两类：可变对象和不可变对象。

在[官方文档](https://docs.python.org/3/glossary.html)中，可变性的定义如下：

> immutable
> 
> An object with a fixed value. Immutable objects include numbers, strings and tuples. Such an object cannot be altered. A new object has to be created if a different value has to be stored. They play an important role in places where a constant hash value is needed, for example as a key in a dictionary.


固定值是可变对象的最根本的属性，因此在Python的赋值语句中，如果左侧为不可变对象，则通常需要创建新的对象，再将名称和新对象绑定。

# 可哈希性（hashable）

## 可变性与可哈希性的关系
