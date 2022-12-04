---
layout: post
title:  POSIX定时器和看门狗实现
author: me
date: 2022-09-15 14:05:05 +0800
categories: learn linux
tags: [C语言, 编程, Linux]
---

## 创建POSIX定时器

可以通过timer_create函数创建POSIX定时器，其中timer_create函数声明如下；

```c
#include <signal.h>           /* Definition of SIGEV_* constants */
#include <time.h>

int timer_create(clockid_t clockid, struct sigevent *restrict sevp,
                timer_t *restrict timerid);

// Link with -lrt.
```

对其中参数依次进行介绍。

### clockid_t clockid

clockid确定定时器所用时钟类型，常见的有以下几种：

1. CLOCK_REALTIME：真实世界时钟，也就是挂钟时间（wall time）
2. CLOCK_MONOTONIC：单调时钟，记录了系统启动以来的ticks数
3. CLOCK_BOOTTIME：类似CLOCK_MONOTONIC，不过系统休眠（suspended）的时间也被计算在内
4. CLOCK_PROCESS_CPUTIME_ID：进程CPU时钟，记录了该进程所有线程消耗的CPU时间
5. CLOCK_THREAD_CPUTIME_ID：线程CPU时钟，记录了该线程消耗的CPU时间
6. CLOCK_REALTIME_ALARM：对应CLOCK_REALTIME，不过在系统休眠时会唤醒系统（注意调用必须有CAP_WAKE_ALARM，保证能唤醒系统）
7. CLOCK_BOOTTIME_ALARM：类似CLOCK_REALTIME_ALARM会唤醒系统，不过对应的是CLOCK_BOOTTIME

具体可见下面宏的定义：

```c
#ifdef __USE_POSIX199309
/* Identifier for system-wide realtime clock.  */
# define CLOCK_REALTIME			0
/* Monotonic system-wide clock.  */
# define CLOCK_MONOTONIC		1
/* High-resolution timer from the CPU.  */
# define CLOCK_PROCESS_CPUTIME_ID	2
/* Thread-specific CPU-time clock.  */
# define CLOCK_THREAD_CPUTIME_ID	3
/* Monotonic system-wide clock, not adjusted for frequency scaling.  */
# define CLOCK_MONOTONIC_RAW		4
/* Identifier for system-wide realtime clock, updated only on ticks.  */
# define CLOCK_REALTIME_COARSE		5
/* Monotonic system-wide clock, updated only on ticks.  */
# define CLOCK_MONOTONIC_COARSE		6
/* Monotonic system-wide clock that includes time spent in suspension.  */
# define CLOCK_BOOTTIME			7
/* Like CLOCK_REALTIME but also wakes suspended system.  */
# define CLOCK_REALTIME_ALARM		8
/* Like CLOCK_BOOTTIME but also wakes suspended system.  */
# define CLOCK_BOOTTIME_ALARM		9
/* Like CLOCK_REALTIME but in International Atomic Time.  */
# define CLOCK_TAI			11

/* Flag to indicate time is absolute.  */
# define TIMER_ABSTIME			1
#endif
```

### struct sigevent *restrict sevp

struct sigevent结构体用于异步程序中的信号通知机制，若展开则相关内容较多，本处只做简要介绍。

其结构体可被视作如下：

```c
#include <signal.h>

union sigval {            /* Data passed with notification */
    int     sival_int;    /* Integer value */
    void   *sival_ptr;    /* Pointer value */
};

struct sigevent {
    int    sigev_notify;  /* Notification method */
    int    sigev_signo;   /* Notification signal */
    union sigval sigev_value;
                            /* Data passed with notification */
    void (*sigev_notify_function)(union sigval);
                            /* Function used for thread
                            notification (SIGEV_THREAD) */
    void  *sigev_notify_attributes;
                            /* Attributes for notification thread
                            (SIGEV_THREAD) */
    pid_t  sigev_notify_thread_id;
                            /* ID of thread to signal
                            (SIGEV_THREAD_ID); Linux-specific */
};
```

sigev_signo是被用作通知的具体信号，具体可以参见信号相关介绍。

sigev_notify为通知方法，常用的有以下几种：

- SIGEV_SIGNAL：通过信号通知该进程
- SIGEV_NONE： 不通知，但可以通过timer_gettime函数获知当前定时器状态
- SIGEV_THREAD：通知时会先创建一个线程，再将信号传给相应线程

其定义如下：

```c
/* `sigev_notify' values.  */
enum
{
  SIGEV_SIGNAL = 0,		/* Notify via signal.  */
# define SIGEV_SIGNAL	SIGEV_SIGNAL
  SIGEV_NONE,			/* Other notification: meaningless.  */
# define SIGEV_NONE	SIGEV_NONE
  SIGEV_THREAD,			/* Deliver via thread creation.  */
# define SIGEV_THREAD	SIGEV_THREAD

  SIGEV_THREAD_ID = 4		/* Send signal to specific thread.
				   This is a Linux extension.  */
#define SIGEV_THREAD_ID	SIGEV_THREAD_ID
};
```

当采用SIGEV_THREAD方式时，必须定义sigev_notify_function，作为其线程的通知处理函数。

其余参数和具体内容可参见手册页[^sigevent]的说明。

sevp可以填NULL，此时代表sigev_notify为SIGEV_SIGNAL，sigev_signo为SIGALRM且sigev_value.sival_int为timer ID。

### timer_t *restrict timerid

timer_id为创建定时器的ID（实际上被定义为void *），新建timer_t的数据结构，将&timer_t传入即可。

## 设置POSIX定时器时间

通过timer_settime可以设定定时器的时间（首次过期时间，循环过期时间）。

该函数声明如下：

```c
#include <time.h>

int timer_settime(timer_t timerid, int flags,
                    const struct itimerspec *restrict new_value,
                    struct itimerspec *restrict old_value);
```

其中timerid即为创建时timer_create的timerid，flags通常填0，表示为相对时间，在某些情况下需要填TIMER_ABSTIME，表示绝对时间。

new_value和old_value都时表示定时器的首次过期时间和循环过期时间，其中new_value为本次赋予定时器的首次过期时间和循环过期时间。old_value通常填NULL，如果不为NULL则会保存定时器之前的首次过期时间和循环过期时间（即本次要覆盖的）。

其中struct itimerspec的结构如下所示：

```c
struct timespec {
    time_t tv_sec;                /* Seconds */
    long   tv_nsec;               /* Nanoseconds */
};

struct itimerspec {
    struct timespec it_interval;  /* Timer interval */
    struct timespec it_value;     /* Initial expiration */
};
```

其中首次过期时间new_value->it_value，则代表取消定时器。

## 利用POSIX定时器的看门狗实现

根据以上内容，即可以利用POSIX定时器实现看门狗，其中注意设置的是CLOCK_MONOTONIC，避免真实时间由于时间同步等原因发生更改，而使得看门狗运行出错。

```c
#define _GNU_SOURCE

#include <signal.h>
#include <time.h>

const struct itimerspec watchdogInterval = {{2, 0}, {2, 0}};

timer_t watchdogTimer;

void SetupWatchdog(void) {
  struct sigevent alarmEvent = {};

  alarmEvent.sigev_notify = SIGEV_SIGNAL;

  alarmEvent.sigev_signo = SIGALRM;
  alarmEvent.sigev_value.sival_ptr = &watchdogTimer;

  int result = timer_create(CLOCK_MONOTONIC, &alarmEvent, &watchdogTimer);
  result = timer_settime(watchdogTimer, 0, &watchdogInterval, NULL);
}

// Must be called periodically
void ExtendWatchdogExpiry(void) {
  // check that application is operating normally
  // if so, reset the watchdog
  timer_settime(watchdogTimer, 0, &watchdogInterval, NULL);
}
```

## 参考

* [man7.org/timer_create(2)](https://man7.org/linux/man-pages/man2/timer_create.2.html)

* [Microsoft/Use a system timer as a watchdog](https://learn.microsoft.com/en-us/azure-sphere/app-development/watchdog-timer)

## 脚注

[^sigevent] [man7.org/sigevent(7)](https://man7.org/linux/man-pages/man7/sigevent.7.html)
