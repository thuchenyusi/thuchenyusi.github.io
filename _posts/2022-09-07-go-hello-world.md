---
layout: post
title:  Hello, 世界 in Go语言
author: me
date:   2022-09-07 20:51:14 +0800
categories: learn golang
tags: [Go语言, 编程]
---

> 本文基于Go 1.19版本。
{: .prompt-info }

## hello, world

按照惯例，我们从“hello, world”程序开始，创建helloworld.go文件如下：

```go
package main

import "fmt"

func main() {
    fmt.Println("Hello, 世界")
}
```

## go run和go build

输入如下命令：

```bash
go run hellworld
```

将会输出“Hello, 世界”，和许多较新的语言一样，Go语言原生支持Unicode，无需做特殊处理即可处理所有国家的语言。

Go是编译型的语言，采用如下命令生成可执行文件，并可直接执行：

```bash
go build helloworld.go
./helloworld
```

## package和import

Go代码是通过package来组织的，在每个源文件开始都会用package指明属于哪个package。在本例中helloworld.go便属于package main。

package main和其他package有所不同，它通常用来定义一个独立的可执行程序。

在package后，紧跟着import来导入所需要的包，本例中即导入了fmt。

## 函数

在Go语言中，函数的声明为如下格式：

```go
func main(argc int, argv []string) int {

}
```

从前往后分别为func关键字、函数名、参数列表、返回值列表和函数体。

和C语言不同，函数的返回值列表定义在函数名和参数列表的后方。这种定义方式对一些复杂的声明看起来会比C风格的定义方式要更为直观。

考虑[Go's Declaration Syntax](https://go.dev/blog/declaration-syntax)中介绍的某个例子，函数的参数和返回值均含有函数指针：

C：

```C
int (*(*fp)(int (*)(int, int), int))(int, int)
```

Go：

```Go
f func(func(int,int) int, int) func(int, int) int
```

这种靠后的声明显然更为直观，实际上Go的变量声明也是将参数类型后置，同样在许多场景下会显得更为直观而少歧义，例如指针声明。

## 格式

Go对格式要求较为严格，但同时也提供了gofmt工具以自动化格式代码。go的子命令fmt也是gofmt的封装，用来格式化指定包里或当前文件夹中的所有文件。

## 参考

- The Go Programming Language
