---
layout: post
title:  Linux 60秒性能分析
author: me
date: 2022-12-07 23:34:40 +0800
categories: learn linux
tags: [编程, Linux, 性能分析]
---

> 本文主要参考Netflix的技术博客。
{: .prompt-info }

在读Brendan Gregg的*BPF Performance Tools*，其中提到他和Nefilx性能团队曾经发表的一篇关于性能分析的文章[^1]，讲述了对一个新Linux系统性能分析的前60秒应该进行哪些步骤。

尽管国内有不少网站已经翻译转载过那篇原始博文，但为了加深自己的印象，还是重新将相关内容转述一下（也算一种重复造轮子吧www）。

## 简要清单

```bash
uptime
dmesg | tail
vmstat 1
mpstat -P ALL 1
pidstat 1
iostat -xz 1
free -m
sar -n DEV 1
sar -n TCP,ETCP 1
top
```

## uptime

## dmesg | tail

## vmstat 1

## mpstat -P ALL 1

## pidstat 1

## iostat -xz 1

## sar -n DEV 1

## sar -n TCP,ETCP 1

## top

## 脚注

[^1]: [Linux Performance Analysis in 60,000 Milliseconds](https://netflixtechblog.com/linux-performance-analysis-in-60-000-milliseconds-accc10403c55)