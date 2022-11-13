---
layout: post
title:  原子操作和内存序
author: me
date:   2022-11-13 22:24:06 +0800
categories: learn clang
tags: [C语言, 编程, C++]
---

## 原子类型

## 原子操作

### 锁无关

## 内存序

在C和C++中，定义了如下6种内存序，用于解决内存一致性问题。

```c
typedef enum memory_order {
    memory_order_relaxed,
    memory_order_consume,
    memory_order_acquire,
    memory_order_release,
    memory_order_acq_rel,
    memory_order_seq_cst
} memory_order;
```

### relaxed

### consume

### acquire

### release

### acq_rel

### seq_cst
