title:Linux Time
date: 2014-02-16 16:46
category: linux
tags: linux, time
author: yboren

时间在任何地方都是很重要的，在计算机中更是如此。计算机是一种精巧的工具，它的正常运行需要极其严格的时序来控制，它的效率用单位时间的工作能力来衡量，可以说时间是整个计算机的基石。有时间计算机就知道当前时刻该做什么事情，当前的事情该用多长时间，如果没做完下次应该何时继续，是不是应该分配比这一次更多的时间来做它以保证它更快的完成，如果当前事情到了指定的时间还没做完，应该怎么把它放到一边，然后让后面安排的事情进入处理。计算机靠着时间正常运行，也把自己的时间贡献给各种任务，从而完成一件件的具体工作。

linux作为一个操作系统，管理着所有的硬件设备，要高效的工作，了解整个时间机制是如何工作的是很重要的，主要是这几个方面，硬件，软件（内核中和硬件寄存器打交道的部分和提供给应用程序使用的系统调用），程序接口，实用工具。


#硬件时钟电路
电路相关的基本上就是一些固定频率振荡器和计数器电路，像晶振，8254芯片等这些东西组成的定时电路。由于硬件的发展，一般计算机系统中都存在着不止一套的定时器电路，越老的电路虽然精度不一定好，但是使用最普遍，几乎所有的计算机上都存在，最近最先进的虽然精度要好得多，但是只存在于最新的硬件上，不具有普遍性，只能在一定范围内使用，所以linux中同时支持好多种定时器，然后系统会根据精度来挑选一下最好用的给系统的定时机制使用。
##实时时钟（RTC）
所有的PC都包含这个时钟，Real Time Clock（RTC），这个电路不在CPU中，一般和BIOS在一起，有独立的电池供电，所以即使电脑被切断电源，这个时钟还是准确的。
RTC会在IRQ8上发出周期性的中断，频率在2-8192Hz之间，RTC也可以被编程，当达到某个计数值的时候激活IRQ8。
linux中只用RTC来获取时间和日期，不过，可以通过操作/dev/rtc文件来对RTC进行编程，内核中是通过0x70/0x71 这两个I/O端口来访问RTC的，linux的系统实用工具也是直接作用于这两个端口来设置时钟。

##可编程间隔计数器（PIT）
可编程间隔计数器（Programmable Interval Timer），PIT被编程后以固定频率发起时钟中断，一般在IBM
PC上是一个使用0x40-0x43端口的8254芯片。linux一般把PIT编程为以大约1000Hz的频率向IRQ0发起时钟中断，即每1ms发起一次时钟中断。这样一个时间间隔就叫一个节拍（tick），节拍是一个很重要的概念。一般来说，短的节拍能够产生高精度的定时器，高精度的定时器在执行同步I/O多路利用时，能够保持较快响应时间，但是短的节拍需要CPU在内核态花费较多的时间，也就是在用户态花费较少的时候，因此，用户程序运行会稍慢一点，所以节拍长短的选择是一种折中。

##时间戳计数器（TSC）
TSC（Time Stamp
Counter）是x86系列处理器的一个64位的寄存器，所有的x86系列处理器都会有一个CLK的输入端，接收来自外部晶振的时钟信号，TSC会在每个时钟信号到来的时候加1，比如当前时钟节拍是1GHz的，那么每个纳秒TSC寄存器都会加1。所以这里有一个问题，这里依靠的是时钟频率，现在的CPU都有变频技术，在不需要大量运算的时候，CPU会自动降频以减小耗电量，所以这里关键的地方就是要确定时钟频率。

##ACPI电源管理定时器
ACPI电源管理定时器（ACPI PMT）几乎所有基于ACPI电源管理的主板上都有，它的时钟信号是大约3.58Hz的固定频率，它其实上是一个简单的计数器，在每个时钟节拍到来的时候加一，通过I/O端口来读取计数器的值。它的优越性在于它的时钟信号是固定频率的，这就比TSC要好，因为现代的操作系统或者BIOS都能动态的调整CPU的运行频率，这时TSC可能会发生时间偏差，而ACPI
PMT不会，这都是缘于它的固定的高频率，另外一方面，高频率也能测量非常小的时间间隔。

##高精度事件定时器（HPET）
高精度事件定时器是由Intel和Microsoft联合开发的一种新型定时器芯片，它实际上包含了很多可以被内核使用的硬件定时器，linux内核2.6已经支持HPET。

这种新的定时器芯片主要包含了8个32位或64位的独立计数器。每个计数器由自己的时钟信号所驱动，且时钟信号的频率必须至少为10MHz，因此上计数器的精度可以到100ns，至少每100ns增长一次。任何计数器最多可以与32个定时器相关联，每个定时器由一个比较器和匹配寄存器组成，设定的时间存在匹配寄存器中，通过比较器发现计数器的值和匹配寄存器的值一样，则发出一次硬件中断，表示一个定时事件。

HPET定时器功能强大，一般如果存在的话，总是会被内核优先使用，作为系统的首先硬件定时器电路。

#计时体系结构
linux kernel必须要执行一些与时间相关的动作，比如：

* 更新系统启动时间

* 更新时间和日期

* 检查进程运行时间，是否超过时间片，是否需要启动进程调度

* 更新源使用统计数

* 检查每个软计时器

实现这些功能，linux内核需要一组数据结构和操作函数，这些就组成了linux系统的计时体系。

##linux内核计时体系的数据结构

###定时器对象

定时器对象是一种抽象，定义一个定时器对象是为了能统一的描述计算机上可能存在的定时器资源（上面描述的那些硬件电路），数据结构类型是timer\_opts，该类型主要由定时器名称和四个标准方法组成。

如下所示


定时器最重要的方法是mark\_offset和get\_offset。mark\_offset方法由时钟中断处理程序调用，记录每个节拍到来的准确时间，get\_offset访求使用记录下来的值来计算上一次时钟中断以来经过的时间。这两个方法组合起来，可以让linux的计时体系能够达到子节拍的分辨度，就是说计时精度可以比节拍更高。

由于一个计算机中存在着好几种硬件定时电路，内核到底使用哪一种呢，从最优的角度想，内核肯定会选择一个最好的来使用，毕竟，不用也浪费嘛。这个工作linux会在初始化的时候做好，并保存在cur\_timer中，初始化的时候，cur\_timer先指向一个空对象，timer\_none，然后，内核调用select\_timer开始选择一个最好的定时器，这里就有个优先级的顺序，在上面介绍的这么几种定时器，内核会按照一定的优先级来先，如果有HPET当然要用，其次是ACPI电源管理定时器，然后TSC，最后的垫底方案，选择PIT，因为每个计算机上都能保证有PIT。

###jiffies变量
jiffies变量是一个计数器，保存着系统自启动以来产生的节拍数，在每个时钟发生时（每个节拍）它的值加1。如果jiffies变量值是32位的，大概50天左右就会回绕到0,但是内核有相关的宏能够处理这种情况。如果jiffies是个64位的，那么大概几十亿年都不会用完，这样看起来会更好，因为内核需要知道节拍数，而32位的回绕了后就丢失了信息，而64位的就不存在这个问题。实际上由于在32位体系中不能直接对一个64位的变量进行访问，需要分两次32位的访问从而完成对一个64位变量的访问，这中间要保证同步，需要使用到锁，结果反而影响了效率，所以实际上jiffies是作为一个jiffies\_64变量的低32位的，这样更新时只操作32位，读取时用一个顺序锁来保证同步。

###xtime变量
xtime变量存放当前时间和日期，实际是一个timespec类型的数据结构，有两个字段，tv\_sec和tv\_nsec，一个存放自1970年1月1日以来经过的秒数，一个存放自上一秒以来开始经过的纳秒数。

xtime通常每个节拍更新一次，如果节拍是1ms的话，那么一秒会更新大概1000次。xtime\_lock锁用来保护对xtime变量的访问，防止发生竞争，同样xtime\_lock也保护jiffies\_64变量。

##linux内核定时体系的函数
###初始化阶段
以单处理器为例，前面提到，在内核初始化阶段，会调用timer\_init()函数来建立计时体系，一般来言，主要做这么几件事情

1. 初始化xtime变量。利用get\_coms\_time()从实时时钟上读取自1970年1月1日以来经过的秒数。设置xtime的tv\_nsec字段，这样使得即将发生的jiffies变量溢出与tv\_sec字段的增加保持一致，也就是说，它将落到秒的范围内。

2. 初始化wall\_to\_monotonic变量。这个变量同xtime一样是timespec类型，只不过它存放将被加到xtime上的秒数的纳秒数，以此来获得单向（只增加）的时间流。

3. 如果内核支持HPET，将调用hpet\_enable()函数来确认ACPI固件是否探测到了该芯片并对HPET的第一个定时器编程使其以每秒1000次的频率引发IRQ0处的中断。如果不支持HPET，内核将使用PIT，PIT已经在init\_IRQ()中初始化。

4. 调用timer\_select()函数来挑选系统中可用的最好的定时器资源，并设置cur\_timer变量指向该定时器资源对应的定时器对象的地址。

5. 调用setup\_irq(0, &irq0)来创建与IRQ0相对应的中断门，IRQ0引脚线连接着系统时钟中断源（PIT或者HPET）。从现在起，timer\_interrupt()函数会在每个节拍到来时被调用。

###时钟中断处理程序
timer\_interrupt()函数是时钟中断处理程序，它主要做以下几件事情

1. 在xtime\_lock顺序锁上产生一个write\_seqlock来保护与定时相关的内核变量。

2. 执行cur\_timer定时器对象的mark\_offset方法，这个由于定时器对象的不同，可能有四种情况。
>*  cur\_timer指向timer\_hpet对象：这种情况下，HPET作为时钟中断源。mark\_offset方法检查自上一个节拍以来是否丢失时钟中断，在这种不太可能发生的情况下，它会相应地更新jiffies\_64变量，接着，记录下HPET周期计数器的当前值。
>* cur\_timer指向timer\_pmtmr对象：这种情况下，PIT芯片作为时钟中断源，但是内核使用APIC电源管理定时器以更高的分辨度来测量时间。mark_offset方法检查自上一个节拍以来有没有丢失时钟中断，如果丢失则更新jiffies\_64变量，然后，它记录APIC电源管理定时器计数器的当前值。
>* cur\_timer指向timer\_tsc对象：这种情况下，PIT芯片作为时钟中断源，但是内核使用TSC以更高分辨度来测量时间。mark\_offset执行的与上一种情况相同：检查自上一个节拍以来有没有丢失时钟中断，如果丢失则更新jiffies\_64变量，然后它纪录TSC计数器的当前值。
>* cur\_timer指向timer\_pit对象：这种情况下，PIT芯片作为时钟中断源，除此这外没有别的定时器。mark\_offset什么也不做。

3. 调用do\_timer\_interrupt()，do\_timer\_interrupt()函数执行以下操作：
>1. 使jiffies\_64变量加1.
>2. 调用update\_times()来更新系统的时间和日期，并计算当前系统负载。
>3. 调用update\_process\_times()函数为本地CPU执行几个与定时相关的计数操作。
>4. 调用profile\_tick()函数来同步系统时钟。
>5. 如果使用外部时钟来同步系统时钟，则每隔660s调用一次set\_rtc\_mmss()来调整实时时钟。

4. 调用write\_sequnlock()释放xtime\_lock顺序锁。

5. 返回1,表示中断已经有效处理过了。

##软定时器和延迟函数
定时器是一种常用的软件功能，定时器就是说给定一个时间间隔，在这个时间间隔用完的将来的某个时刻，调用某个事先确定好的函数。超时时间表示与定时器相关的时间间隔用完的那个时刻。

一般来说，一个定时器要有一个字段，表示定时器需要多长时间到期。这个字段初始值就是jiffies加上合适的节拍数，然后内核在检查定时器时会比较当前jiffies值与定时器存的值，当jiffies大于或者等于定时器中的字段时，表示定时器到期。

linux中主要有两种定时器，动态定时器(dynamic timer)和间隔定时器(interval timer)。第一种内核使用，第二种可由用户态进程使用。

###动态定时器
linux的动态定时器存放在一个叫timer\_list的结构中，重要是两个字段，expires和function。expires字段给出定时器的到期时间，时间用节拍数表示。function用来表示在定时器到期时执行的函数地址，有一个data字段用来给function传递参数。其它字段用来将动态定时器组织起来。

	struct timer_list {
		struct list_head entry;
		unsigned long expires;
		struct tvec_base *base;
		void (*function)(unsigned long);
		unsigned long data;
		int slack;
	};

####动态定时器的数据结构
linux存放动态定时器使用到了链表，但是又不是放在单独的链表中，因为那样在每个时钟节拍去扫描长链表效率太差，而且维护这样一个排序链表本身也比较费时，插入和删除都比较费时间。

linux设计了一种巧妙的数据结构来解决这个问题，按expires的值把定时器分为五个级别，每次只检查最低级别的定时器（定时时间比较短的定时器），当低级别的定时器扫描完一遍后，代表时间已经过去了一段时间，这时可能需要从上一级别降级一些定时器到这一级别来，然后再依次处理。这样就比较巧妙的解决了效率问题，每次只扫描为数不多的链表。

主要的数据结构是这样的，有一个叫

	struct tvec {
		struct list_head vec[TVN_SIZE];
	};
	
	struct tvec_root {
		struct list_head vec[TVR_SIZE];
	};
	
	struct tvec_base {
		spinlock_t lock;
		struct timer_list *running_timer;
		unsigned long timer_jiffies;
		unsigned long next_timer;
		struct tvec_root tv1;
		struct tvec tv2;
		struct tvec tv3;
		struct tvec tv4;
		struct tvec tv5;
	};

tv1-5分别表示五级定时器链表，tv1是一个tvec\_root类型，它包含一个vec数组，这个数组由256个list\_head元素组成，即由256个定时器链表组成，这256个链表分别表示了在马上到来的255个节拍内要到期的定时器。tv2-4的数据结构是tvec类型，该类型有一个数组vec，这个数组由64个list\_head元素组成，它们分别表示了在即将到来的2^14-1、2^20-1和2^26-1节拍内要到期的定时器。tv5与前面的字段几乎相同，唯一的区别就是vec数组的最后一项是一个大expires字段值的定时器链表。

struct tvec\_base数据中，timer\_jiffies字段的值表示需要检查的定时器的最早到期时间，如果这个值与jiffies一样，说明定时器没有积压；如果小于jiffies，则说明前几个节拍有压下来的定时器需要处理（有大量的中断处理函数时可以定时函数会没来得及执行）。这个字段在系统启动时被设置成jiffies的值，且只有run\_timer\_softirq()函数能增加它的值。

####动态定时器的处理
由于动态定时器的数据结构比较复杂，所以不是由时钟中断处理函数来处理的，2.6中是由可延迟函数来执行的，由TIMER\_SOFTIRQ软中断执行，是run\_timer\_softirq()函数，主要干这么几件事情：

1. 把与本CPU相关的tvec\_base的地址放到本地base变量中。

2. 获得base->lock自锁锁并禁止本地中断。

3. 执行一个while循环，当base->timer\_jiffies大于jiffies时停止。循环执行的内容包括：

>1. 计算base->tv1中链表的索引，该索引保存着下一次将要处理的定时器
	index = base->timer\_jiffies & 255;

>2. 如果索引值为0,说明base->tv1中的所有链表都已经被检查过了，所以为空，于是调用cascade()函数来从上级定时器来补充一些到tv1中来
	if (!index &&
			(!cascade(base, &base->tv2, (base->timer_jiffies>>8)&63)) &&
				(!cascade(base, &base->tv3, (base->timer_jiffies>>14)&63)) &&
					!cascade(base, &base->tv4, (base->timer_jiffies>>20)&63))
			cascade(base, &base->tv5, (base->timer_jiffies>>26)&63);
考虑第一次调用 cascade()的情况,它接收base、base->tv2的地址、base->tv2中链表的索引作为参数。cascade将base->tv2中链表上的所有动态定时器移到base->tv1的适当链表上。然后如果所有base->tv2中的链表不为空，它返回一个正值，否则返回0，那么cascade将再一次被调用，把base->tv3中的某个链表上包含的定时器填充到base->tv2上，如此等等。

>3. base->timer\_jiffies加1

>4. 对于base->tv1.vec\[index\]链表上的每一个定时器，执行它所对应的定时器函数。对于链表上的每个timer\_list元素t，具体的步骤是：

>>1. 将t从base-tv1的链表上去除

>>2. t.base为NULL

>>3. 释放base->lock自旋锁，允许本地中断

>>4. 传递t.data为参数，执行t.function

>>5. 获得base->lock自旋锁，并禁止本地中断

>>6. 如果链表中有其他定时器，继续处理。

>5. 链表上的所有定时器已经被处理，继续下一次while循环

4. 最外面的while循环结束，本次需要处理的定时器均已经处理完毕

5. 释放base->lock自旋锁并允许本地中断

要说明的是，由于jiffies和timer\_jiffies的值经常是一样的，所以一般情况下外层的while循环只执行一次。

###动态定时器的应用
nanosleep()系统调用中就用到了定时动态定时器，nanosleep()调用的是sys\_nanosleep()，它接收一个指向timespec结构的指针作为参数，并将调用进程挂起直到特定的时间间隔用完。它首先调用copy\_from\_user()将包含在timespec（用户态）的值复制到局部变量t中，接着执行如下代码
	current->state = TASK\_INTERRUPTIBLE;
	ramaining = schedule\_timeout(timespec\_to\_jiffies(\&t) + 1);
timespec\_to\_jiffies()函数首先把存放在timespec结构中的时间转换成节拍数，为了保险，会给计算出的节拍数加上一个节拍。

在schedule\_timeout中使用到了动态定时器，代码如下：

	struct timer_list timer;
	unsigned long expire = timeout+jiffies;
	init_timer(&timer);
	timer.expires = expire;
	timer.data = (unsigned long)current;
	timer.function = process_timeout;
	add_timer(&timer);
	schedule();
	del_singleshot_timer_sync(&timer);
	timeout = expire - jiffies;
	return (timeout < 0? 0: timeout);

当schedule()被调用，就选择另外一个进程执行；当前一个进程恢复运行的时，该函数就删除这个动态定时器。最后一句的return语句，返回0表示定时器到期，返回timeout表示如果进程因某些其他原因被唤醒，到延时到期时还剩余的节拍数。

当延时到期时，内核执行下列函数

	void process_timeout(unsigned long __data)
	{
		wake_up_process((task_t *)__data);
	}

process_timeout()函数将进程描述符指针作为它的参数，然后该描述符指的进程被唤醒。一旦进程被唤醒，它就继续执行nanosleep()系统调用。如果schedule\_timeout()返回的值表示进程延时到期，系统调用到期，否则系统调用重新启动。

###延时函数
有时内核需要等待一个比较短的时间间隔，比如说不超过几毫秒，这时，无需使用动态定时器，因为使用定时器有比较大的设置开销和最小等待时间（1ms），所以这时内核会使用一些延时函数。

延时函数有udelay()和ndelay()，区别是前者接收一个微秒级的时间间隔作为参数，而后者接收一个纳秒级的时间间隔为参数。

这两个函数大概是这个样子

	void udelay(unsigned long usecs)
	{
	unsigned long loops;
	loops = (usecs*HZ*current_cpu_data.loops_per_jiffy)/1000000;
		cur\_timer->delay(loops);
	}
	void ndelay(unsigned long nsecs)
	{
		unsigned long loops;
		loops = (nsecs*HZ*current_cpu_data.loops_per_jiffy)/1000000000;
		cur\_timer->delay(loops);
	}

这里又提到了cur\_timer对象，当初始化完成后，内核会通过执行calibrate\_delay()来确认一个节拍里有多少次loop，把这个值存在current\_cpu\_data.loops\_per\_jiffy变量中，这样udelay()和ndelay()就能把微秒和纳秒转换成loops。

##与定时相关的系统调用
###time()和gettimeofday()系统调用
time()被gettimeofday()替代，gettimeofday()系统调用由函数sys\_gettimeofday()来实现，实际上这个函数又调用do\_gettimeofday()，它执行如下动作：

1. 为读操作获取xtime\_lock锁
2. 调用cur\_timer定时器对象的get\_offset方法来确定自上一次时钟中断以来所走过的微秒数

	usec = cur_timer->get_offset()

3. 如果定时器中断丢失，则加上相应的延迟

	usec += (jiffies - wall_jiffies) * 1000;

4. 为usec加上前1秒内走过的微秒数

	usec += (xtime.tv_nsec / 1000);

5. 将xtime的内容复制到系统调用参数tv指定的用户态空间缓冲区中，并给微秒字段加上usec

	tv->tv_sec = xtime->tv_sec;
	tv->tv_usec = usec;

6. 在xtime\_lock顺序锁上调用read\_seqretry()，如果另外一条内核控制路径获取了xtime\_lock，则跳回到1
7. 检查微秒字段是否溢出，如果溢出则调整

	while(tv->tv_usec > 1000000){
		tv->tv_sec += 1;
		tv->tv_usec -= 1000000;
	}
