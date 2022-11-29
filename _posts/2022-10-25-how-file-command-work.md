---
layout: post
title:  C语言：宏
author: me
date:   2022-10-25 15:59:00 +0800
categories: learn linux
tags: [Linux, 编程]
---

file命令通过如下三个步骤判断文件类型。

## 检查文件系统（filesystem tests）
先通过stat(2)查看是否为本系统通用的类型（如目录），头文件<sys/stat.h>中保存有相关定义。

## 检查魔数（magic tests）
许多类型的文件开头是特定的魔数，魔数和文件的对应关系通常会记录在/etc/magic或/usr/share/misc/magic。

## 检查语言类型（language tests）
最后file会通过检查文件首部是否含有特定字符串来判断语言类型。

例如如果存在 *.br* 关键字，那么该文件很可能是troff(1)输入文件，而有关键字 *struct* 则该文件可能是C语言程序源码。

可以看出，这样的判断方式是不准确，本步骤的检测相对之前两步更不可靠（也正因如此，本步骤最后执行）。

本步骤也会检测一些杂项类型，例如tar(1)归档文件、JSON文件等。

## 参考

- [ file(1) ](https://man7.org/linux/man-pages/man1/file.1.html)
- [ Fine Free File Command ](http://www.darwinsys.com/file/)
- [ file/file ](https://github.com/file/file)
