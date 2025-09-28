import base64

import dotenv

dotenv.load_dotenv()
import time
import asyncio
import streamlit as st
from agents import Agent, Runner, SQLiteSession, WebSearchTool, FileSearchTool, ImageGenerationTool
from openai import OpenAI

client = OpenAI()
VECTOR_STORE_ID = "vs_68d91090f5808191a127939ee78b28a7"

if "agent" not in st.session_state:
    st.session_state["agent"] = Agent(
        name="ChatGPT Clone",
        model="gpt-4o-mini",
        instructions="""
        당신은 유용한 조수입니다.
        다음 도구에 액세스할 수 있습니다:
            - Web Search Tool: 사용자가 학습 데이터에 없는 질문을 할 때 이 도구를 사용하세요. 사용자가 현재 또는 미래의 이벤트에 대해 질문할 때 이 도구를 사용하여 답을 모른다고 생각되면 먼저 웹에서 검색해 보세요.
            - File Search Tool: 사용자가 자신과 관련된 사실에 대해 질문할 때 이 도구를 사용합니다. 또는 특정 파일에 대해 질문할 때 사용합니다.
            - Image generation tool: 사용자가 이미지 생성을 요청할 때 이 도구를 사용합니다.
        """,
        tools=[
            WebSearchTool(),
            FileSearchTool(
                vector_store_ids=[VECTOR_STORE_ID],
                max_num_results=3
            ),
            ImageGenerationTool(
                tool_config= {
                    "type" : "image_generation",
                    "quality": "medium",
                    "size": "1024x1024",
                    "output_format": "jpeg",
                    "partial_images": 3
                }
            )
        ],
    )
agent = st.session_state["agent"]

if "session" not in st.session_state:
    st.session_state["session"] = SQLiteSession(
        "chat-history",
        "chat-gpt-clone-memory.db",
    )
session = st.session_state["session"]


async def paint_history():
    messages = await session.get_items()

    for message in messages:
        if "role" in message:
            with st.chat_message(message["role"]):
                if message["role"] == "user":
                    content = message["content"]
                    if isinstance(content, str):
                        st.write(content)
                    elif isinstance(content, list):
                        for part in content:
                            if "image_url" in part:
                                st.image(part["image_url"])
                else:
                    if message["type"] == "message":
                        st.write(message["content"][0]["text"].replace("$", "\$"))
        if "type" in message:
            message_type = message["type"]
            if message_type == "web_search_call":
                with st.chat_message("ai"):
                    st.write("🔍 Searched the web...")
            elif message_type == "file_search_call":
                with st.chat_message("ai"):
                    st.write("🔍 Searched the file...")
            elif message_type == "image_generation_call":
                image = base64.b64decode(message["result"])
                with st.chat_message("ai"):
                    st.image(image)


def update_status(status_container, event):
    status_messages = {
        "response.web_search_call.completed": ("✅ Web search completed.", "complete"),
        "response.web_search_call.in_progress": (
            "🔍 Starting web search...",
            "running",
        ),
        "response.web_search_call.searching": (
            "🔍 Web search in progress...",
            "running",
        ),
        "response.file_search_call.completed": ("✅ File search completed.", "complete"),
        "response.file_search_call.in_progress": (
            "🔍 Starting File search...",
            "running",
        ),
        "response.file_search_call.searching": (
            "🔍 File search in progress...",
            "running",
        ),
        "response.image_generation_call.generating": (
            "🎨 Drawing image...",
            "running",
        ),
        "response.image_generation_call.in_progress": (
            "🎨 Drawing image...",
            "running",
        ),
        "response.completed": (" ", "complete"),
    }

    if event in status_messages:
        label, state = status_messages[event]
        status_container.update(label=label, state=state)


asyncio.run(paint_history())


async def run_agent(message):
    with st.chat_message("ai"):
        status_container = st.status("⏳", expanded=False)
        text_placeholder = st.empty()
        image_placeholder = st.empty()
        response = ""

        stream = Runner.run_streamed(
            agent,
            message,
            session=session,
        )

        async for event in stream.stream_events():
            if event.type == "raw_response_event":
                update_status(status_container, event.data.type)
                if event.data.type == "response.output_text.delta":
                    response += event.data.delta
                    text_placeholder.write(response.replace("$", "\$"))
                elif event.data.type == "response.image_generation_call.partial_image":
                    image = base64.b64decode(event.data.partial_image_b64)
                    image_placeholder.image(image)
                elif event.data.type == "response.complete":
                    image_placeholder.empty()


prompt = st.chat_input(
    "Write a message for your assistant",
    accept_file=True,
    file_type=["txt", "jpeg", "jpg", "png"],
)

if prompt:
    # 파일을 먼저 로드 시킨다
    for file in prompt.files:
        if file.type.startswith("text/"):
            with st.chat_message("ai"):
                with st.status("⏳Uploading file..") as status:
                    uploaded_file = client.files.create(
                        file=(file.name, file.getvalue()),
                        purpose="user_data"
                    )
                    status.update(label="⏳Attaching file..")
                    client.vector_stores.files.create(
                        vector_store_id=VECTOR_STORE_ID,
                        file_id=uploaded_file.id,
                    )
                    status.update(label="✔ File uploaded.", state="complete")
        elif file.type.startswith("image/"):
            with st.status("⏳Uploading image..") as status:
                file_bytes = file.getvalue()
                base64_bytes = base64.b64encode(file_bytes).decode("utf-8")
                data_uri = f"data:{file.type};base64,{base64_bytes}"
                asyncio.run(
                    session.add_items([{
                        "role": "user",
                        "content": [{
                            "type": "input_image",
                            "detail": "auto",
                            "image_url": data_uri
                        }],
                    }])
                )
                status.update(label="✔ Image uploaded.", state="complete")
            with st.chat_message("user"):
                st.image(data_uri)

    if prompt.text:
        with st.chat_message("human"):
            st.write(prompt.text)
        asyncio.run(run_agent(prompt.text))

with st.sidebar:
    reset = st.button("Reset memory")
    if reset:
        asyncio.run(session.clear_session())
    st.write(asyncio.run(session.get_items()))
