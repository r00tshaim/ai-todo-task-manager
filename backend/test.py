from pydantic import BaseModel, Field
from dotenv import load_dotenv

from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from trustcall import create_extractor

load_dotenv()


class Memory(BaseModel):
    content: str = Field(description="The main content of the memory. For example: User expressed interest in learning about French.")

class MemoryCollection(BaseModel):
    memories: list[Memory] = Field(description="A list of memories about the user.")

# Initialize the model
model = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)

# Create the extractor
trustcall_extractor = create_extractor(
    model,
    tools=[Memory],
    tool_choice="Memory",
    enable_inserts=True,
)


# Instruction
instruction = """Extract memories from the following conversation:"""

# Conversation
conversation = [HumanMessage(content="Hi, I'm Shaim."), 
                AIMessage(content="I love playing footvall in rainy weather."), 
                HumanMessage(content="This morning I had a walk in early morning.")]

# Invoke the extractor
result = trustcall_extractor.invoke({"messages": [SystemMessage(content=instruction)] + conversation})



# Conversation
updated_conversation = [HumanMessage(content="Hi, I'm Shaim."), 
                AIMessage(content="I love playing footvall in rainy weather."), 
                HumanMessage(content="This morning I had a walk in early morning."),
                AIMessage(content="Thats great! I also enjoy morning walks, especially when the weather is nice."),
                HumanMessage(content="I am interested in learning about Generative AI.")]


# Update the instruction
system_msg = """Update existing memories and create new ones based on the following conversation:"""

# We'll save existing memories, giving them an ID, key (tool name), and value
tool_name = "Memory"
existing_memories = [(str(i), tool_name, memory.model_dump()) for i, memory in enumerate(result["responses"])] if result["responses"] else None

print("Existing Memories:", existing_memories)

# Invoke the extractor
result = trustcall_extractor.invoke({"messages": [SystemMessage(content=system_msg)] + updated_conversation,
                                     "existing": existing_memories})

# Print the result
# Messages contain the tool calls
for m in result["messages"]:
    m.pretty_print()