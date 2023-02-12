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

在60s内，可以通过运行如下10个命令，以对系统资源使用情况和运行进程有一个高层次（high-level）的了解。

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

```bash
$ uptime 
23:51:26 up 21:31, 1 user, load average: 30.02, 26.43, 19.02
```

该命令用于快速查看机器的平均负载（load average）。

所谓平均负载，表示等待运行的任务数。在Linux系统中，包括等待运行在CPU上的进程和被不可中断IO（通常为磁盘I/O）所阻断的进程。

输出的3个数字为1分钟、5分钟和15分钟内的平均负载情况。

通过输出的数字能粗略的对负载相对时间的变化情况进行估计。

## dmesg | tail

```bash
$ dmesg | tail
[1880957.563150] perl invoked oom-killer: gfp_mask=0x280da, order=0, oom_score_adj=0
[...]
[1880957.563400] Out of memory: Kill process 18694 (perl) score 246 or sacrifice child
[1880957.563408] Killed process 18694 (perl) total-vm:1972392kB, anon-rss:1953348kB, file-rss:0kB
[2320864.954447] TCP: Possible SYN flooding on port 7001. Dropping request.  Check SNMP counters.
```

该步骤输出最近的10条系统信息（如果有的话）。

这些信息中可能包含了导致性能问题的错误，如上面例子中的内存不足问题和TCP丢包问题。

dmesg并非直接和性能相关，有时不会去特意查看dmesg中输出的系统信息。然而原作者特别指出，不要忘记这一步骤，dmesg信息往往值得查看。

## vmstat 1

## mpstat -P ALL 1

```bash
$ mpstat -P ALL 1
Linux 3.13.0-49-generic (titanclusters-xxxxx)  07/14/2015  _x86_64_ (32 CPU)

07:38:49 PM  CPU   %usr  %nice   %sys %iowait   %irq  %soft  %steal  %guest  %gnice  %idle
07:38:50 PM  all  98.47   0.00   0.75    0.00   0.00   0.00    0.00    0.00    0.00   0.78
07:38:50 PM    0  96.04   0.00   2.97    0.00   0.00   0.00    0.00    0.00    0.00   0.99
07:38:50 PM    1  97.00   0.00   1.00    0.00   0.00   0.00    0.00    0.00    0.00   2.00
07:38:50 PM    2  98.00   0.00   1.00    0.00   0.00   0.00    0.00    0.00    0.00   1.00
07:38:50 PM    3  96.97   0.00   0.00    0.00   0.00   0.00    0.00    0.00    0.00   3.03
[...]
```

该命令输出每个CPU的CPU时间详情，有助于发现不同CPU间的不均衡问题。例如单个CPU使用率较高可能是某但线程程序使用了较多CPU导致的。

## pidstat 1

```bash
$ pidstat 1
Linux 3.13.0-49-generic (titanclusters-xxxxx)  07/14/2015    _x86_64_    (32 CPU)

07:41:02 PM   UID       PID    %usr %system  %guest    %CPU   CPU  Command
07:41:03 PM     0         9    0.00    0.94    0.00    0.94     1  rcuos/0
07:41:03 PM     0      4214    5.66    5.66    0.00   11.32    15  mesos-slave
07:41:03 PM     0      4354    0.94    0.94    0.00    1.89     8  java
07:41:03 PM     0      6521 1596.23    1.89    0.00 1598.11    27  java
07:41:03 PM     0      6564 1571.70    7.55    0.00 1579.25    28  java
07:41:03 PM 60004     60154    0.94    4.72    0.00    5.66     9  pidstat

07:41:03 PM   UID       PID    %usr %system  %guest    %CPU   CPU  Command
07:41:04 PM     0      4214    6.00    2.00    0.00    8.00    15  mesos-slave
07:41:04 PM     0      6521 1590.00    1.00    0.00 1591.00    27  java
07:41:04 PM     0      6564 1573.00   10.00    0.00 1583.00    28  java
07:41:04 PM   108      6718    1.00    0.00    0.00    1.00     0  snmp-pass
07:41:04 PM 60004     60154    1.00    4.00    0.00    5.00     9  pidstat
^C
```

pidstat显示每个进程的CPU使用细目，相比于top，pidstat输出的数据不会被刷新走，有助于后续分析数据。

在如上的例子中，2个java程序消耗了大部分的CPU时间，其中每个java程序大约消耗了16个CPU。

## iostat -xz 1

```bash
$ iostat -xz 1
Linux 3.13.0-49-generic (titanclusters-xxxxx)  07/14/2015  _x86_64_ (32 CPU)

avg-cpu:  %user   %nice %system %iowait  %steal   %idle
          73.96    0.00    3.73    0.03    0.06   22.21

Device:   rrqm/s   wrqm/s     r/s     w/s    rkB/s    wkB/s avgrq-sz avgqu-sz   await r_await w_await  svctm  %util
xvda        0.00     0.23    0.21    0.18     4.52     2.08    34.37     0.00    9.98   13.80    5.42   2.44   0.09
xvdb        0.01     0.00    1.02    8.94   127.97   598.53   145.79     0.00    0.43    1.78    0.28   0.25   0.25
xvdc        0.01     0.00    1.02    8.86   127.79   595.94   146.50     0.00    0.45    1.82    0.30   0.27   0.26
dm-0        0.00     0.00    0.69    2.32    10.47    31.69    28.01     0.01    3.23    0.71    3.98   0.13   0.04
dm-1        0.00     0.00    0.00    0.94     0.01     3.78     8.00     0.33  345.84    0.04  346.81   0.01   0.00
dm-2        0.00     0.00    0.09    0.07     1.35     0.36    22.50     0.00    2.55    0.23    5.62   1.78   0.03
[...]
^C
```

## sar -n DEV 1

## sar -n TCP,ETCP 1

## top

## 脚注

[^1]: [Linux Performance Analysis in 60,000 Milliseconds](https://netflixtechblog.com/linux-performance-analysis-in-60-000-milliseconds-accc10403c55)