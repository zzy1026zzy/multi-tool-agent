### 激活.venv环境

```bash
.\.venv\Scripts\Activate.ps1
```



### 任务 1・工具调用 web_search

#### 是什么：

一个网络搜索工具，模型需要实时信息时调用。文件是 `tools/web_search.py`。

不清楚「工具」「function calling」是怎么回事？`docs/背景知识.md` 第 1 节讲了：为什么大模型需要工具、为什么模型只「点单」不执行代码、`description` 为什么是关键。

在流程里的位置：和 `weather` 走的是同一套工具循环（见 4.1），本质就是再加一个工具。

#### 思路：

先把工具循环、开关、写测试这套流程跑顺。照 `weather.py` 的样子，`run()` 返回一个字符串就行。先用 mock 数据把链路跑通，确认工具能被调到，再去考虑接真实搜索 API。

写完别忘了改开关，骨架里 `is_available()` 的 TODO 已经提示了。

最小验证：起后端，问助手「搜一下今天的新闻」，右边仪表栏会出现调用 `web_search` 的记录（用 `python main.py` 则会打印 `[调用工具 web_search ...]`）。`/api/capabilities` 的 `tools` 里也应该能看到 `web_search`。

使⽤博查平台的 API：配置BOCHA_API_KEY，BOCHA_SEARCH_URL=https://api.bochaai.com/v1/web-search

#### 易踩坑：

- 实现了 `run()`，却忘了把 `is_available()` 改成 `True`，结果工具被隐藏，模型永远不调。
- `description` 写得太笼统（比如只写「搜索」），模型判断不出什么时候该用。描述要让模型一看就知道适用什么场景。

### 任务 2・⻓期记忆

#### 是什么：
跨会话记住⽤⼾的稳定事实和偏好，⽐如「我叫⼩明」「我是 Python ⼯程师」，落盘到
data/memory_store.json 。⽂件是 memory/long_term.py 。
不熟悉「⼤模型为什么会失忆」「记忆到底是什么」？ docs/背景知识.md 第 2 节讲清了：模型为什么⽆状态、
两层记忆分别治哪种「忘」、为什么⻓期记忆要按全局 USER_ID ⾛，以及任何记忆都在做的「写」和「读」两
件事。

在流程⾥的位置： agent.chat_stream() 每轮开头调 recall(user_msg) ，把相关事实注⼊上下⽂；每轮结尾调
remember(user_msg, reply) ，抽取并存下事实。接⼝（ recall 、 remember 、 all_facts ）定义在
memory/base.py ，没实现时由 NoOpLongTermMemory 兜底。

#### 思路：
对照 short_term.py 看⼀个记忆模块怎么存、何时调 LLM、怎么注⼊，⻓期记忆是同⼀套思路，只是换成
跨会话的事实。四个待实现的⽅法各管⼀摊： _load 和 _save 管落盘， recall 管召回， remember 管⽤ LLM
从对话⾥抽稳定事实。先⽤⻣架建议的最简单策略（关键词召回、全量注⼊）跑通，向量召回留作进阶。

有⼀点要特别注意：记忆是全局的。它按固定的 USER_ID （⻅ config.py ）存，所有对话窗⼝共享同⼀份，和每
个窗⼝的 session_id 是分开的。这正是换个窗⼝也能记得的原因。写完把模块顶部的 ENABLED 改成 True ，
factory 会⾃动启⽤。

最⼩验证：起后端，在 A 窗⼝告诉它「我叫⼩明」，再新建⼀个 B 窗⼝问「我叫什么」。它答得出来，就成了，因为⻓
期记忆是全局共享的。也可以 curl http://localhost:8000/api/memory/任意id 看 facts 列表，或者看右边
仪表栏的「记住了什么」。

#### 易踩坑：

_save() 直接覆盖⽂件，会把别的 user 的数据冲掉。正确做法是先读出整体 dict，只更新⾃⼰这⼀项，再
写回。

把记忆按 session_id 存，换个窗⼝就忘了，跨会话的效果也没了。它要按全局 USER_ID 存。
同⼀条事实反复存进去，记得去重。