import asyncio
import os
import sys
import pathlib
from dotenv import load_dotenv
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from semantic_kernel.connectors.ai.open_ai import OpenAIChatPromptExecutionSettings
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.connectors.mcp import MCPSsePlugin
from semantic_kernel.contents import ChatHistory
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.functions import KernelArguments

async def main():
    current_dir = pathlib.Path(__file__).parent
    env_path = current_dir / ".env"
    load_dotenv(env_path)

    kernel = Kernel()

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set.")
    
    model_id = "gpt-4.1" 
    service = OpenAIChatCompletion( ai_model_id = model_id, api_key=api_key) 
    kernel.add_service(service)

    settings = OpenAIChatPromptExecutionSettings()
    settings.function_choice_behavior = FunctionChoiceBehavior.Auto()

    async with (MCPSsePlugin(
       name="weather",
       description="Weather plugin",
       url=os.getenv("MCP_WEATHER_URL")
    ) as weather_plugin,
    MCPSsePlugin(
        name="stocks",
        description="Stock plugin",
        url=os.getenv("MCP_STOCKS_URL")
    ) as stocks_plugin):
        # Register the MCP plugin with the kernel
        try:
            kernel.add_plugin(weather_plugin, plugin_name="weather")
            kernel.add_plugin(stocks_plugin, plugin_name="stocks")
        except Exception as e:
            print(f"Error: Could not register the MCP plugin: {str(e)}")
            sys.exit(1)
        
        # Create a chat history with system instructions
        history = ChatHistory()
        history.add_system_message(
            "You are a meteorologist assistant that can answer questions about the weather in a given location."
            "You have access to get the current weather and forecast for the next 7 days from the MCP Plugin."
            "You are also a financial assistant that can answer questions about stocks"
            "You have the ability to get the current stock price, news, and financial news from the MCP Plugin."
        )
        
        # Define a simple chat function
        chat_function = kernel.add_function(
            plugin_name="chat",
            function_name="respond", 
            prompt="{{$chat_history}}"
        )
        
        print("\n┌────────────────────────────────────────────┐")
        print("│ Andreoli's Assistant ready with MCP Weather   │")
        print("└────────────────────────────────────────────┘")
        print("Type 'exit' to end the conversation.")
        print("\nExample questions:")
        print("- What is the sum of 3 and 5?")
        print("- Can you multiply 6 by 7?")
        print("- If I have 20 apples and give away 8, how many do I have left?")
        
        while True:
            user_input = input("\nUser:> ")
            if user_input.lower() == "exit":
                break
                
            # Add the user message to history
            history.add_user_message(user_input)
            
            # Prepare arguments with history and settings
            arguments = KernelArguments(
                chat_history=history,
                settings=settings
            )
            
            try:
                # Stream the response
                print("Assistant:> ", end="", flush=True)
                
                response_chunks = []
                async for message in kernel.invoke_stream(
                    chat_function,
                    arguments=arguments
                ):
                    chunk = message[0]
                    if isinstance(chunk, StreamingChatMessageContent) and chunk.role == AuthorRole.ASSISTANT:
                        print(str(chunk), end="", flush=True)
                        response_chunks.append(chunk)
                
                print()  # New line after response
                
                # Add the full response to history
                full_response = "".join(str(chunk) for chunk in response_chunks)
                history.add_assistant_message(full_response)
                
            except Exception as e:
                print(f"\nError: {str(e)}")
                print("Please try another question.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExiting the Math Assistant. Goodbye!")
    except Exception as e:
        print(f"\nError: {str(e)}")
        print("The application has encountered a problem and needs to close.") 
