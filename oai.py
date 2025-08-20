# In your oai.py file

import os
from openai import AzureOpenAI
from langchain_core.messages import (
    BaseMessage,
    SystemMessage,
    HumanMessage,
    AIMessage,
)

class AzureLLMWrapper:
    """
    This is the stable wrapper that produced the "no error" log.
    It correctly converts various LangChain message formats for input
    and returns a simple AIMessage for the output.
    """
    def __init__(self, client, deployment_name):
        self.client = client
        self.deployment_name = deployment_name
        self.tools = None

    def __call__(self, messages, temperature=0.7, max_tokens=8000):
        # This debug print helps see what the agent is sending
        print(f"--- 래 AzureLLMWrapper: Received raw messages for conversion: {messages} ---")

        converted_messages = []
        for msg in messages:
            # This logic handles both message objects and tuples
            if isinstance(msg, BaseMessage):
                if isinstance(msg, AIMessage):
                    role = "assistant"
                elif isinstance(msg, SystemMessage):
                    role = "system"
                else: # Default to user for HumanMessage, etc.
                    role = "user"
                converted_messages.append({"role": role, "content": msg.content})

            elif isinstance(msg, tuple) and len(msg) == 2:
                role, content = msg
                role_map = {"human": "user", "ai": "assistant", "system": "system"}
                converted_messages.append({"role": role_map.get(role.lower(), "user"), "content": str(content)})

            else:
                # Fallback for any other unexpected format
                print(f"Warning: Unhandled message type: {type(msg)}. Treating as user message.")
                converted_messages.append({"role": "user", "content": str(msg)})


        print(f"--- 래 AzureLLMWrapper: Calling OpenAI with correctly formatted messages: {converted_messages} ---")

        response = self.client.chat.completions.create(
            model=self.deployment_name,
            messages=converted_messages,
            temperature=temperature,
            max_tokens=max_tokens
        )

        ai_response_content = response.choices[0].message.content
        print(f"--- 래 AzureLLMWrapper: Received response from AI: {ai_response_content} ---")

        # It worked because it returned a simple AIMessage that the agent could parse for text.
        return AIMessage(content=ai_response_content)


    def bind_tools(self, tools):
        """Stores the tools so the agent can use them."""
        print(f"--- 래 AzureLLMWrapper: Binding tools: {[tool.name for tool in tools]} ---")
        self.tools = tools
        return self


def create_azure_llm():
    """Initializes and returns the Azure OpenAI LLM WRAPPER for agent use."""
    print("--- 🤖 Creating Azure LLM with Wrapper ---")
    client = AzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
    )
    deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
    return AzureLLMWrapper(client, deployment_name)