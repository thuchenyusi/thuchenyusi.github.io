---
layout: post
title:  Go语言的函数
author: me
date:   2022-09-19 23:46:16 +0800
categories: learn golang
tags: [Go语言, 编程]
---

> 本文基于Go 1.19版本。
{: .prompt-info }
## 声明
Go语言中，函数的声明由名字、形参列表、返回列表（可选）和函数体构成，注意Go对代码格式要求比较严格：

```go
func name(parameter-list) (result-list) {
    body
}
```

### 声明的组成成分

函数的名字和其他名字有着同样的规则，由字母或下划线开头，后面可以跟任意数量的字符、数字和下划线，并且区分大小写。

函数的形参列表由一组变量的参数名和参数类型构成。

函数的形参变量由函数的实参的值进行初始化，为函数最外层作用域的局部变量。

函数的返回列表制定了返回值的类型和名字（可选）。如果函数的没有返回值或只有一个未命名的返回值是，返回列表的圆括号可以省略。

命名的返回值会根据变量类型初始化为相应的0值，和形参变量一样，同为函数最外层作用域的局部变量。

存在返回列表时，无论返回值有没有得到命名，函数必须显式地以return结束。如下，return不能省略：

```go
func sub(x int, y int) (z int) {
    z = x - y
    return
}
```

### 相同类型简写

当多个形参或返回值的类型相同时，可以采用简写的方式，只写一次类型。如下的两个声明完全等价：

```go
func f(i, j, k, int, s, t string ) {
    /* ... */
}

func f(i int, j int, k int, s string, t string) {
    /* ... */
}
```

### 函数签名及其等价性

函数的类型被称为函数签名，如果两个函数的形参列表和返回列表相同（形参和返回值的名称不影响），则认为两个函数的类型是相同的。如下的两个函数签名即是相同的：

```go
func add(a int, b int) int {
    return a + b
}

func sub(x int, y int) (z int) {
    z = x - y
    return
}
```

### 无默认参数

Go语言中没有默认参数值，也不能指定实参名，因此GO语言中需要提供实参来对应函数中的每个形参，并保持调用顺序的一致。以下在Python中的语法，Go中不存在：

```python
def func(a=2, b=3, c=5):
    return a + 2*b + 3*c


# 2+2*3+3*5 = 23
print(func())
# 1+2*3+3*5 = 22
print(func(1))
# 2+2*4+3*1 = 13
print(func(c=1, b=4, a=2))
```

### 按值传递

和C语言类似的，Go语言的实参也是按值传递的，修改函数的形参变量并不会影响被调用者提供的实参。当然，可以通过指针、slice等特定形参变量间接修改实参的变量。

### 无函数体的声明

Go语言中存在没有函数体的函数声明，这样的函数是由其他语言实现的：

```go
package math

func Sin(x float64) float64 // 使用汇编语言实现
```

## 递归

和许多语言类似，Go支持递归，递归过程中也会有函数调用栈的入栈和出栈。但与固定长度大小的函数调用栈的语言不同，Go同时还支持可变长度的函数调用栈，函数调用栈的大小随着使用增加可达到1GB，因此通常情况下不用担心函数递归时常会担心的栈溢出问题。

## 多返回值

## 错误处理

Go语言采用返回值的方式进行错误处理，这类似于C语言的处理方式。函数将错误信息返回给调用者，由调用者决定如何处理，很多情况下调用者也不清楚应该如何处理该错误，那么往往会再将该错误返回值传递下去，通过层层返回到逻辑上便于处理的层级进行处理。以GOPL中的例子为例：

```go
func findLinks(url string) ([]string, error) {
    resp, err := http.Get()
    if err != nil {
        return nil, err
    }
    if resp.StatusCode != http.StatusOK {
        resp.Body.Close()
        return nil, fmt.Errorf("getting %s %s", url, resp.Status)
    }
    doc, err := html.Parse(resp.Body)
    resp.Body.Close()
    if err != nil {
        return nil, fmt.Errof("parsing %s as HTML: %v", url, err)
    }
    return visit(nil, doc), nil
}
```

从例子中可以看到Go语言中关于错误处理的几个通用做法：

1. 错误为最后1个返回值，且为error类型。
2. 当函数允许成功时，错误返回为nil。
3. 对于子函数的错误，如果不好处理，会返回给上级函数。

不过也并非所有函数的错误类型均为error类型，如果错误情况只有一种，则通常用布尔类型进行表示。如下所示：

```go
value, ok := cache.Lookup(key)
if !ok {
    // ...cache[key]不存在
}
```

其中返回值ok即为布尔型，正确代表无错误发生。

Go语言并未采用类似try-catch的异常机制来处理通常的错误，因为Go语言的设计者认为try-catch的异常机制将导致栈跟踪信息难以理解。但这并不代表Go语言没有异常机制，Go语言存在panic-recover机制，不过这套机制只被用于处理程序Bug导致的预料外的结果，对于可预见的错误还是应该通过通常的错误处理方式进行处理。

和C进行比较的话，C语言的返回值往往既能表示正确的值又能表示错误的值，光靠返回值有时不足以表明其具体错误类型，因此可能还需要通过其他方式将错误信息传递出来，比如常见的通过errno传递错误信息。

```c
if (somecall() == -1) {
    printf("somecall() failed\n");
    if (errno == ...) { ... }
}
```

而Go语言中，多返回值的特性，本身就使得错误返回值能够只需表达错误情况，而不需要传递程序正常运行所需要的返回值。error类型本身也可以传递字符串作为错误标识，其表达力足够清晰表达大部分错误。error是接口类型，其包含返回错误信息的方法：

```go
type error interface {
    Error() string
}
```

error包也很简单，只有4行。如下所示：

```go
package errors
func New(text string) error { return &errorString{text} }
type errorString struct { text string }
func (e *errorString) Error() string { return e.text }
```

其中errorString对string做了简单封装，目的是避免后续布局变更。而满足error接口的是*errorString指针，这样就能使得每次New分配的error实例都不相等。

```go
fmt.Println(errors.New("EOF") == errors.New("EOF")) // "false"
```

## 宕机
