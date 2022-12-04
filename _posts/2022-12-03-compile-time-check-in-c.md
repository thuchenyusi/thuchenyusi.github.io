---
layout: post
title:  C语言编译期的静态断言
author: me
date:   2022-12-03 17:10:44 +0800
categories: learn clang
tags: [C, C++]
---

> 本文基于C17(C18)版本。相关内容在后续版本中可能有较大变化，文中对部分有变化的情况做了说明。
{: .prompt-info }

相比于C++在编译期（complie-time）的强大能力（如C++的模板元编程是图灵完备的，而这正是在编译期进行的），C语言要逊色许多，但我们仍然能够在编译期进行基本的计算和断言工作，无论是将计算移至编译期所带来的，从而能够将某些运行时才能发现的问题。

## 常量表达式

首先介绍常量表达式（Constant expressions，标准6.6节）的概念，所谓常量表达式，就是可以在翻译阶段（translation）而不是运行阶段（runtime）求值，并可以用在任何一个可以使用常量（constant）的地方的表达式。

> 常量（constant）和常变量（constant variable）是不同的概念。
{: .prompt-warning }

什么样的表达式可以在C语言的翻译阶段求值呢？

首先该表达式不应包含赋值、自增、自减、函数调用或逗号运算符（这些运算符都可能具有副作用），除非它们被包含在一个不被求值的子表达式中（如作为sizeof的操作数，在sizeof(x++)中并不会去对x++求值，只会获取其类型）。每个常量表达式都应求值为一个常量，该常量在其类型的可表示值范围内。

常量表达式被分为三种类型：

1. 整型常量表达式，其类型为整型。其常量表达式的操作数必须为整型常量、枚举常量、字符常量、结果为整型的sizeof表达式，_Alignof表达式和被强转的浮点。其中浮点必须被强转为整型，除非被用作sizeof表达式和_Alignof表达式的操作数。
2. 算术常量表达式，其必须为算术类型。与整型常量表达式要求相似，不过放开了对浮点数的支持。
3. 地址常量表达式，其为指针类型。地址常量表达式是空指针、指向静态存储区的指针或指向函数的指针。该类型常量应该由取地址运算符生成，或由整型常量强转为指针得到。在地址常量表达式中，可以有数组下标运算符[]、点运算符.和箭头运算符->。

> 继C++之后，C23草案也引入了新的constexpr关键字，但仅限于对象（Object），并不能用于修饰函数的支持。
{: .prompt-notice }

常量表达式有什么作用呢？最常见的，就是常量表达式被用于具备静态和线程存储期对象的初始化语句（如语句中的初始化列表、数组的下标等都需要填写常量表达式）。

需要注意的是，尽管常变量和使用常变量的符合一定条件的表达式是可以在编译期求值的，但C标准中并没有规定其可以做常量表达式。与之相对应的，C++对此则是明确支持的。

如下面的例子，其中在所注释的语句在C++中是完全合法的，但在C中通常是不合法的：

```c
#define ARR_SIZE 4
const int arr_size = 4;

int global_arr0[ARR_SIZE];
int global_arr1[ARR_SIZE] = {0, 1, 2, 3};

// 不合法，静态数组在上电时分配内存，其大小需要在编译期计算
// int global_arr2[arr_size];
// int global_arr3[arr_size] = {0, 1, 2, 3};

int main() {
  int local_num;

  // 合法，编译时能确定数组大小
  int local_arr0[ARR_SIZE];
  int local_arr1[ARR_SIZE + 1] = {0, 1, 2, 3};
  int local_arr2[sizeof(int)] = {0, 1, 2, 3};
  static int staitc_arr[sizeof(local_num++)] = {0, 1, 2, 3};

  local_num = 2;
  // C11以后合法，非静态和线程存储期的数组在运行main函数时才会初始化，在此之前arr_size被求值即可
  int local_arr3[arr_size];
  int local_arr4[local_num];

  // 不合法，编译时需要保存{0, 1, 2, 3}
  // int local_arr5[arr_size] = {0, 1, 2, 3};

  // 合法，&global_arr0[0]为地址常量，函数名退化为函数指针
  static int *static_pointer0 = &global_arr0[0];
  static int (*static_pointer1)() = main;

  // 合法，非静态和线程存储期，在运行main函数时能求值即可
  int *local_pointer0 = &local_num;

  return 0;
}

```

## 静态断言

在C11以后，标准中正式引入了静态断言，可用于在编译期做检查。

```c
// _Static_assert为关键字
_Static_assert(constant-expression, string-literal);
// static_assert为指向_Static_assert的宏，与C++兼容，包含在<assert.h>中
static_assert(constant-expression, string-literal);
```

当constant-expression（必须为整型常量表达式）等于0时，会打印string-literal的消息。示例如下：

```c
// requires /std:c11 or higher
#include <assert.h>

enum Items { A, B, C, LENGTH };

int main() {
  // _Static_assert is a C11 keyword
  _Static_assert(LENGTH == 3, "Expected Items enum to have three elements");

  // Preferred: static_assert maps to _Static_assert and is compatible with C++
  static_assert(sizeof(int) == 4, "Expecting 32 bit integers");

  return 0;
}
```

通过静态断言可以在编译期做很多检查，例如VPP代码中的几个例子。

检查数据结构大小：

```c
typedef enum ipsec_sad_flags_t_
{
#define _(v, f, s) IPSEC_SA_FLAG_##f = v,
  foreach_ipsec_sa_flags
#undef _
} __clib_packed ipsec_sa_flags_t;

STATIC_ASSERT (sizeof (ipsec_sa_flags_t) == 2, "IPSEC SA flags != 2 byte");
```

检查内存对齐情况：

```c
typedef struct
{
  CLIB_CACHE_LINE_ALIGN_MARK (cacheline0);

  /* flags */
  ipsec_sa_flags_t flags;

  u8 crypto_iv_size;
  u8 esp_block_align;
  u8 integ_icv_size;

  u8 __pad1[3];

  u32 thread_index;

  u32 spi;
  u32 seq;
  u32 seq_hi;
  u64 replay_window;
  u64 ctr_iv_counter;
  dpo_id_t dpo;

  vnet_crypto_key_index_t crypto_key_index;
  vnet_crypto_key_index_t integ_key_index;

  /* Union data shared by sync and async ops, updated when mode is
   * changed. */
  union
  {
    struct
    {
      vnet_crypto_op_id_t crypto_enc_op_id:16;
      vnet_crypto_op_id_t crypto_dec_op_id:16;
      vnet_crypto_op_id_t integ_op_id:16;
    };

    struct
    {
      vnet_crypto_async_op_id_t crypto_async_enc_op_id:16;
      vnet_crypto_async_op_id_t crypto_async_dec_op_id:16;
      vnet_crypto_key_index_t linked_key_index;
    };

    u64 crypto_op_data;
  };

  CLIB_CACHE_LINE_ALIGN_MARK (cacheline1);

  union
  {
    ip4_header_t ip4_hdr;
    ip6_header_t ip6_hdr;
  };
  udp_header_t udp_hdr;

  /* Salt used in CTR modes (incl. GCM) - stored in network byte order */
  u32 salt;

  ipsec_protocol_t protocol;
  tunnel_encap_decap_flags_t tunnel_flags;
  u8 __pad[2];

  /* data accessed by dataplane code should be above this comment */
    CLIB_CACHE_LINE_ALIGN_MARK (cacheline2);

  /* Elements with u64 size multiples */
  union
  {
    struct
    {
      vnet_crypto_op_id_t crypto_enc_op_id:16;
      vnet_crypto_op_id_t crypto_dec_op_id:16;
      vnet_crypto_op_id_t integ_op_id:16;
    };
    u64 data;
  } sync_op_data;

  union
  {
    struct
    {
      vnet_crypto_async_op_id_t crypto_async_enc_op_id:16;
      vnet_crypto_async_op_id_t crypto_async_dec_op_id:16;
      vnet_crypto_key_index_t linked_key_index;
    };
    u64 data;
  } async_op_data;

  tunnel_t tunnel;

  fib_node_t node;

  /* elements with u32 size */
  u32 id;
  u32 stat_index;
  vnet_crypto_alg_t integ_calg;
  vnet_crypto_alg_t crypto_calg;

  /* else u8 packed */
  ipsec_crypto_alg_t crypto_alg;
  ipsec_integ_alg_t integ_alg;

  ipsec_key_t integ_key;
  ipsec_key_t crypto_key;
} ipsec_sa_t;

STATIC_ASSERT_OFFSET_OF (ipsec_sa_t, cacheline1, CLIB_CACHE_LINE_BYTES);
STATIC_ASSERT_OFFSET_OF (ipsec_sa_t, cacheline2, 2 * CLIB_CACHE_LINE_BYTES);
```

检查数据结构是否会造成缓冲区溢出：

```c
/*
 * Ensure that the IPsec data does not overlap with the IP data in
 * the buffer meta data
 */
STATIC_ASSERT (STRUCT_OFFSET_OF (vnet_buffer_opaque_t, ipsec.sad_index) ==
		 STRUCT_OFFSET_OF (vnet_buffer_opaque_t, ip.save_protocol),
	       "IPSec data is overlapping with IP data");
```

可以看出，如果不适用静态断言在编译期做检查，那么就必须在运行时才可能发现相应问题。而如内存对齐这类要求，很可能在修改代码过程中被破坏而未被发现，然而通过静态断言的手段，则能够有效的对此类问题进行检查。

## 参考

* [Open Standards/C - Project status and milestones](https://www.open-std.org/jtc1/sc22/wg14/www/projects)
  
  可公开获取的C标准草案，也是本文主要参考源。

* [GCC/The C Preprocessor](https://gcc.gnu.org/onlinedocs/cpp/index.html)
  
  GCC预处理器的相关说明。
