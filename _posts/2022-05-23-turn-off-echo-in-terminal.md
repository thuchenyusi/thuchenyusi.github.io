---
layout: post
title:  如何关闭Linux终端的回显？
author: me
date:   2022-05-23 11:17:00 +0800
categories: learn linux
tags: [C, Linux, 编程]
---

## 通过shell命令关闭回显

在Linux中通过stty相关指令可以关闭终端的回显，如下所示。

```bash
# turn off echo
stty -echo
# do something
# turn on echo
stty echo
```

如果是为了输入密码的话，也可用read命令的-s选项，如下所示。

```bash
# input your password
read -s password
```

## C语言关闭回显

如果是为了输入密码而关闭回显的话，在C语言中，传统上有getpass函数。

```c
#include <unistd.h>

char *getpass(const char *prompt);
```

但该函数现在已经被认为是过时的（obsolete），man中建议不要使用此函数，而是通过控制termios的ECHO标志来达到目的，这种做法也更为通用。一个简单的示例如下：

```c
#include <stdio.h>
#include <termios.h>

void  getpass(unsigned char *key)
{
    struct termios old;
    struct termios new;
    char pass[32] = {0};

    // save old attr
    tcgetattr(STDIN_FILENO, &old);

    // turn off echo
    new = old;
    new.c_lflag &= ~(ECHO);
    tcsetattr(STDIN_FILENO, TCSANOW, &new);

    if (NULL == fgets(pass, sizeof(pass), stdin))
        pass[0] = '\0';

    // recover old attr
    tcsetattr(STDIN_FILENO, TCSANOW, &old);

    printf("%s", pass);

    return;
}
```
