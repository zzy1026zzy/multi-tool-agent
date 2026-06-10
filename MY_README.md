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

### 任务 3· RAG检索生成

#### 是什么

大模型只会**续写文字**。它没学过的东西——你的私有文档、公司内部资料、训练截止之后的新知识——硬问它，它只会一本正经地编（这就是幻觉）。

RAG（检索增强生成）就是来补这个缺口的：先准备一个可检索的资料库，每次用户提问时，先从库里把最相关的几段查出来、塞进上下文，再让模型照着这些资料回答。这样模型就从「凭记忆瞎猜」变成「照着手头资料说话」，答得准，也能交代出处。

#### 流程
RAG 大概是这个流程：

文档文件
  ↓
chunk_text() 切成小块
  ↓
_llm.embed(chunks) 把每个小块转成向量
  ↓
STORE.add(chunks, embeddings, metadatas) 入库
  ↓
用户提问时，STORE.search() 找最相似的块
  ↓
把命中的文本块交给大模型回答

#### 几个属性分别是什么

1、self.texts: list[str] 存的是原始文本块。

比如 data/docs/知简-价格与套餐.md 被切成了几段，其中一段可能是：

专业版价格为 ¥18/月，或 ¥168/年。，这个字符串就会被放进 self.texts。

它的作用是：搜索命中后，真正返回给大模型看的资料内容。

2、self.embeddings: list[list[float]]
存的是每个文本块对应的向量。

比如上面那段文字经过 embedding 模型后，可能变成：

[0.012, -0.31, 0.88, ...]，实际维度可能是几百或几千维。

它的作用是：用来计算“用户问题”和“文档块”语义上有多像。
问题也会被转成一个向量。然后系统拿“问题向量”和库里每个“文档块向量”算相似度，找出最相关的几段。

3、self.metadatas: list[dict]
存的是每个文本块的附加信息，通常是来源。

比如：

{"doc": "data/docs/知简-价格与套餐.md"}
它的作用是：告诉你这个命中的文本来自哪个文件。

后面 knowledge_base.py 里会用它生成引用来源：

{"doc": h["metadata"].get("doc"), "score": h["score"], "snippet": h["text"][:50]}
前端右侧仪表栏显示“引用来源”，靠的就是这个 metadata。

#### 遇到问题

这个报错的核心原因是：

你用 DeepSeek 的 base_url 去请求 OpenAI 的 embedding 模型 text-embedding-3-small
现在 .env 里是：

OPENAI_BASE_URL=https://api.deepseek.com/v1
CHAT_MODEL=deepseek-v4-flash
EMBEDDING_MODEL=text-embedding-3-small
text-embedding-3-small 是 OpenAI 的 embedding 模型名，但请求发到了：

https://api.deepseek.com/v1/embeddings
DeepSeek 那边找不到这个模型或这个接口，所以返回：

openai.NotFoundError: Error code: 404