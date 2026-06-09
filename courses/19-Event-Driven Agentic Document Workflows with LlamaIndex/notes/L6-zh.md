# L6：用语音给 Agent 反馈

上一课我们用文本反馈完成了人在回路。本节给 Agent 加一对耳朵——把麦克风录音转写后送进 `HumanResponseEvent`。**Workflow 本身不需要改动**——这是它结构设计的红利。

## 1. 先看完整工作流可视化

把 L5 的整套 `RAGWorkflow` 整段贴回来，然后调用：

```python
from llama_index.utils.workflow import draw_all_possible_flows

WORKFLOW_FILE = "workflows/lesson_6.html"
draw_all_possible_flows(RAGWorkflow, filename=WORKFLOW_FILE)
```

可视化图能清楚看到 happy path：

`StartEvent → set_up → parse_form → generate_questions → (扇出) ask_question → fill_in_application → InputRequiredEvent → (外部) HumanResponseEvent → get_feedback → 要么 StopEvent，要么回到 generate_questions`。

## 2. 用 Whisper 把语音转文字

LlamaIndex 内置了 **`WhisperReader`**，专门用来把音频文件转写成 `Document`：

```python
from llama_index.readers.whisper import WhisperReader
import gradio as gr

def transcribe_speech(filepath):
    if filepath is None:
        gr.Warning("No audio found, please retry.")
    audio_file = open(filepath, "rb")
    reader = WhisperReader(
        model="whisper-1",
        api_key=openai_api_key,
    )
    documents = reader.load_data(filepath)
    return documents[0].text
```

值得留意：`WhisperReader` 返回的就是和 RAG 阶段同一种 `Document` 对象，整套生态完全统一。

## 3. 用 Gradio 在 Notebook 里采集麦克风

Gradio 提供了能在 Jupyter 里直接渲染的麦克风组件。先做一个简单版（用全局变量保存结果）：

```python
def store_transcription(output):
    global transcription_value
    transcription_value = output
    return output

mic_transcribe = gr.Interface(
    fn=lambda x: store_transcription(transcribe_speech(x)),
    inputs=gr.Audio(sources="microphone", type="filepath"),
    outputs=gr.Textbox(label="Transcription"),
)

test_interface = gr.Blocks()
with test_interface:
    gr.TabbedInterface([mic_transcribe], ["Transcribe Microphone"])

test_interface.launch(
    share=False,
    server_port=8000,
    prevent_thread_lock=True,
)
```

录制 → 停止 → 提交，文本就会出现，并写入全局变量 `transcription_value`。用完记得 `test_interface.close()`，否则多个 Gradio 实例会抢端口。

## 4. 把它包成可在 Workflow 中等待的 `TranscriptionHandler`

把"录音 → 转写 → 拿到结果"做成一个**异步可 await 的对象**，方便 Workflow 外层调用。核心思路：用 `Queue` 当桥梁，`asyncio.sleep(...)` 轮询：

```python
import asyncio
from queue import Queue

class TranscriptionHandler:
    def __init__(self):
        self.transcription_queue = Queue()
        self.interface = None

    def store_transcription(self, output):
        self.transcription_queue.put(output)
        return output

    def create_interface(self):
        mic_transcribe = gr.Interface(
            fn=lambda x: self.store_transcription(transcribe_speech(x)),
            inputs=gr.Audio(sources="microphone", type="filepath"),
            outputs=gr.Textbox(label="Transcription"),
        )
        self.interface = gr.Blocks()
        with self.interface:
            gr.TabbedInterface([mic_transcribe], ["Transcribe Microphone"])
        return self.interface

    async def get_transcription(self):
        self.interface = self.create_interface()
        self.interface.launch(
            share=False,
            server_port=8000,
            prevent_thread_lock=True,
        )
        while True:
            if not self.transcription_queue.empty():
                result = self.transcription_queue.get()
                if self.interface is not None:
                    self.interface.close()
                return result
            await asyncio.sleep(1.5)
```

- `Queue` 是线程安全的，Gradio 的回调线程往里 `put`，主协程从里 `get`；
- `await asyncio.sleep(1.5)` 让协程让出执行权，不阻塞 Workflow 的其他事件流；
- 拿到结果后立刻 `interface.close()`，下一轮再开一个新的——这样可以在同一个端口反复使用。

## 5. 把语音输入接进 Workflow

外层驱动几乎和 L5 一样，只是把 `input(...)` 换成 `TranscriptionHandler`：

```python
w = RAGWorkflow(timeout=600, verbose=False)
handler = w.run(
    resume_file="./data/fake_resume.pdf",
    application_form="./data/fake_application_form.pdf",
)

async for event in handler.stream_events():
    if isinstance(event, InputRequiredEvent):
        transcription_handler = TranscriptionHandler()
        response = await transcription_handler.get_transcription()
        handler.ctx.send_event(
            HumanResponseEvent(response=response)
        )

response = await handler
print("Agent complete! Here's your final result:")
print(str(response))
```

整个 `RAGWorkflow` 代码**一行都没动**——这是事件驱动架构的好处：人机交互通道是"插拔式"的。

## 6. 跑通后的体验

课堂演示中：

1. 第一轮：`Portfolio` 仍然被错误地填成项目清单；
2. 你对着麦克风说："**The portfolio field should be a URL.**"；
3. Whisper 把这句话转成文字 → 进 `HumanResponseEvent` → LLM 判定 `FEEDBACK`；
4. 工作流回到 `generate_questions`，把这句反馈附加到每个问题里再跑一轮；
5. 第二轮，`Portfolio` 字段已变成 URL；
6. 你再说："**That's great. Good job.**" → LLM 判定 `OKAY` → 工作流结束。

> Laurie 还顺手加了一行 `print(f"Asking question: {ev.query}")` / `print(f"Answer was: {response}")`，让你能看到 Agent 思考时的中间问答。

## 7. 改进方向

把反馈**广播**到每个字段虽然有效，但浪费 token、也可能误导无关字段。生产应用里更好的做法是：

- 让 LLM 先分析"这条反馈针对哪个字段"；
- 仅对相关字段重新生成问题，其它字段直接复用上一轮的答案；
- 或者把"反馈 → 字段"的映射本身做成一个独立的 step / 工具调用。

## 小结

到这里，你已经从零搭出了一个完整的**事件驱动智能文档工作流**：

- 用 Workflow 表达多步骤、可分支、可循环、可并发的流程；
- 用 RAG + LlamaParse 把私有文档变成 Agent 可查询的知识；
- 用 `InputRequiredEvent` / `HumanResponseEvent` 把人塞进回路；
- 用 Whisper + Gradio 实现多模态输入。

恭喜，你做出了一个能听懂语音反馈的 AI Agent！
