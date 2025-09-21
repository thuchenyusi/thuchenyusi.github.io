---
layout: post
title:  原子操作和内存序
author: me
date:   2022-11-13 22:24:06 +0800
categories: learn clang
tags: [C, 编程, C++]
---

> 本文描述基于C、C++中的atomic库。
{: .prompt-info }

### 锁无关

在多线程程序设计中，为了解决数据竞争问题，引入了锁来解决相应问题。但频繁的使用锁，往往会花费大量时间在线程的状态切换上，为了降低系统开销提升性能，人们希望在避免使用锁的情况下编写程序，这也被称作锁无关（lock-free）的程序设计。

## 原子操作

### 原子操作类别

1. 读
2. 写
3. 读-改-写

## 指令重排

编写程序的时候，我们总是下意识的认为，在前面的语句总是比在后面的语句优先执行，这样的下意识通常不会造成什么问题。但如果你所写的程序存在数据竞争，那么必须小心了——在程序逻辑中看起来靠前的语句并不总是靠前执行，造成这种现象的原因就是指令重排。

指令重排通常可被分为两种，一种指令由编译器在编译期进行重排，一种指令由处理器在程序运行时进行重排。

编译器和处理器为什么要做这么复杂的事呢？当然是为了性能，指令重排带来的性能提升是巨大的，我们不因为数据竞争而放弃所有指令重排。既然如此，我们必须要学会如何在指令重排的环境下，写出安全而又高效的程序。

首先，先对两类指令重排方式做简要介绍。

### 编译器重排

### 处理器重排

## 内存序

在C和C++中，定义了如下6种内存序（memory order），用于解决内存一致性问题。

```c++
// since C++11 until C++ 20
typedef enum memory_order {
    memory_order_relaxed,
    memory_order_consume,
    memory_order_acquire,
    memory_order_release,
    memory_order_acq_rel,
    memory_order_seq_cst
} memory_order;

// since C++20
enum class memory_order : /*unspecified*/ {

    relaxed, consume, acquire, release, acq_rel, seq_cst
};
inline constexpr memory_order memory_order_relaxed = memory_order::relaxed;
inline constexpr memory_order memory_order_consume = memory_order::consume;
inline constexpr memory_order memory_order_acquire = memory_order::acquire;
inline constexpr memory_order memory_order_release = memory_order::release;
inline constexpr memory_order memory_order_acq_rel = memory_order::acq_rel;
inline constexpr memory_order memory_order_seq_cst = memory_order::seq_cst;
```

### relaxed

具备松散语义的原子操作函数，不会对指令的重排做限制，当然可以被用于所有原子操作函数中。

### release

具有发布语义的原子操作函数，保证函数前的读写操作，不管是否为原子操作，均不能重排到函数之后；但函数后的读写操作能够重排到函数之前。

发布语义通常用于和获取语义/消费语义配合使用，保证获取语义/消费语义的原子操作函数读到发布语义设置的值后，发布语义前的读写操作全部执行完毕。因此，发布语义只能用于执行“写”或“读-改-写”功能的原子操作函数中。

### acquire

具有获取语义的原子操作函数，保证函数后的读写操作，不管是否为原子操作，均不能重排到函数之前；但函数前的读写操作能够重排到函数之后。

获取语义通常用于和发布语义配合使用，保证获取语义的原子操作函数读到发布语义设置的值后，发布语义前的读写操作全部执行完毕。因此，获取语义只能用于执行“读”或“读-改-写”功能的原子操作函数中。

### consume

具有消费语义的原子操作函数，和获取语义比较接近，但约束更弱一些，其保证函数后与该函数返回值相关的读写操作，不管是否为原子操作，均不能重排到函数之前；但函数前的读写操作能够重排到函数之后。

消费语义通常用于和发布语义配合使用，保证消费语义的原子操作函数读到发布语义设置的值后，发布语义前的读写操作全部执行完毕。因此，消费语义只能用于执行“读”或“读-改-写”功能的原子操作函数中。

### acq_rel

具有发布-获取语义的原子操作函数，则同时具备发布和获取的特点，保证函数前的读写操作，不管是否为原子操作，均不能重排到函数之后；函数后的读写操作，也不会被重排到函数之前。
类似地，发布-获取语义只能用于执行“读-改-写”功能的原子操作函数中。

### seq_cst

顺序一致性语义是约束最严格的原子操作函数，可用在任何原子操作函数中，如果该函数是“读”功能的原子操作，则具备获取语义，如果是“写”功能的原子操作则具备发布语义，如果是“读-改-写”功能的原子操作则具备“发布-获取”语义。

但顺序一致性语义并不局限于此，相对与之前的语义，顺序一致性语义还保证了“单一全序”（single total order）：保障所有使用了memory_order_seq_cst的内存序的写操作对所有处理器看来顺序都是一致的。

在C语言中，对原子变量的读写操作，都具备顺序一致性语义。对于不显示声明内存序的原子操作函数系列，也都使用顺序一致性语义的原子操作。
