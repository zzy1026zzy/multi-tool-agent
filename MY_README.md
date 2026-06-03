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