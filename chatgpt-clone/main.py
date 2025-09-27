import asyncio

import streamlit as st
from agents import Agent, Runner, SQLiteSession

if "agent" not in st.session_state:
    st.session_state["agent"] = Agent(
        name="Chatgpt clone agent",
        instructions="""
        You are a helpful assistant
        """
    )

agent = st.session_state["agent"]

if "session" not in st.session_state:
    st.session_state["session"] = SQLiteSession(
        "chat-database",
        "chat-memory.db"
    )

session = st.session_state["session"]

async def run_agent(message: str):
    stream = Runner.run_streamed(agent, message, session=session)
    async for event in stream.stream_events():
        if event.type == "raw_response_event":
            if event.data.type == "response.output_text.delta":
                with st.chat_message("ai"):
                    st.write(event.data.delta)

prompt = st.chat_input("Write you message for your assistant")
if prompt:
    with st.chat_message("human"):
        st.write(prompt)
    asyncio.run(run_agent(prompt))

with st.sidebar:
    reset = st.button("Reset")
    if reset:
        asyncio.run(session.clear_session())
    st.write(asyncio.run(session.get_items()))


