from typing import Annotated, Any, TypedDict

from langchain_core.messages import AnyMessage, HumanMessage, SystemMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langgraph.types import Command, interrupt

from app.ai.adapters.langchain_tools import (
    to_langchain_cancel_order_tool,
    to_langchain_get_order_status_tool,
    to_langchain_search_knowledge_tool,
    to_langchain_search_products_tool,
)
from app.ai.prompts.ecommerce_agent import ECOMMERCE_AGENT_SYSTEM_PROMPT
from app.ai.tools.cancel_order import CancelOrderTool
from app.ai.tools.get_order_status import GetOrderStatusTool
from app.ai.tools.search_knowledge import SearchKnowledgeTool
from app.ai.tools.search_products import SearchProductsTool
from app.schemas.ai import AIChatResponse

default_checkpointer = InMemorySaver()


class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    answer: str
    requires_confirmation: bool


class LangGraphAIService:
    def __init__(
        self,
        llm,
        search_products_tool: SearchProductsTool,
        search_knowledge_tool: SearchKnowledgeTool,
        get_order_status_tool: GetOrderStatusTool,
        cancel_order_tool: CancelOrderTool,
        checkpointer: Any | None = None,
    ):
        self.read_tools = [
            to_langchain_search_products_tool(search_products_tool),
            to_langchain_search_knowledge_tool(search_knowledge_tool),
            to_langchain_get_order_status_tool(get_order_status_tool),
        ]

        self.read_tool_names = {
            tool.name for tool in self.read_tools
        }

        self.write_tools = [
            to_langchain_cancel_order_tool(cancel_order_tool),
        ]

        self.write_tool_names = {
            tool.name for tool in self.write_tools
        }

        self.tools = [
            *self.read_tools,
            *self.write_tools,
        ]

        self.llm_with_tools = llm.bind_tools(self.tools)

        self.checkpointer = checkpointer or default_checkpointer

        self.graph = self._build_graph()

    async def _call_model(
        self,
        state: AgentState,
    ) -> dict:
        messages = [
            SystemMessage(
                content=ECOMMERCE_AGENT_SYSTEM_PROMPT
            ),
            *state["messages"],
        ]
        
        response = await self.llm_with_tools.ainvoke(messages)

        update = {
            "messages": [response],
            "requires_confirmation": False,
        }

        if not response.tool_calls:
            update["answer"] = response.content

        return update

    def _build_graph(self):
        builder = StateGraph(AgentState)

        builder.add_node(
            "agent",
            self._call_model,
        )

        builder.add_node(
            "read_tools",
            ToolNode(self.read_tools),
        )

        builder.add_node(
            "write_tools",
            ToolNode(self.write_tools),
        )

        builder.add_node(
            "confirmation",
            self._request_confirmation,
        )

        builder.add_node(
            "cancel_action",
            self._cancel_action,
        )

        builder.add_edge(
            START,
            "agent",
        )

        builder.add_conditional_edges(
            "agent",
            self._route_tool_call,
            {
                "read_tools": "read_tools",
                "confirmation": "confirmation",
                "end": END,
            },
        )

        builder.add_edge(
            "write_tools",
            "agent",
        )

        builder.add_edge(
            "cancel_action",
            END,
        )

        builder.add_edge(
            "read_tools",
            "agent",
        )

        return builder.compile(
            checkpointer=self.checkpointer
        )


    def _route_tool_call(
        self,
        state: AgentState,
    ) -> str:
        last_message = state["messages"][-1]

        tool_calls = getattr(
            last_message,
            "tool_calls",
            [],
        )

        if not tool_calls:
            return "end"

        tool_call = tool_calls[0]
        tool_name = tool_call["name"]

        if tool_name in self.write_tool_names:
            return "confirmation"

        if tool_name in self.read_tool_names:
            return "read_tools"

        raise ValueError(
            f"Unknown tool requested: {tool_name}"
        )

    def _request_confirmation(
        self,
        state: AgentState,
    ) -> Command:
        last_message = state["messages"][-1]
        tool_call = last_message.tool_calls[0]

        approved = interrupt(
            {
                "question": "Do you want to confirm this action?",
                "tool": tool_call["name"],
                "arguments": tool_call["args"],
            }
        )

        if approved:
            return Command(goto="write_tools")

        return Command(goto="cancel_action")

    def _cancel_action(
        self,
        state: AgentState,
    ) -> dict:
        return {
            "messages": [],
            "answer": "The action was not completed.",
            "requires_confirmation": False,
        }

    async def chat(
        self,
        message: str,
        conversation_id: str,
        confirm_action: bool | None = None,
    ) -> AIChatResponse:
        config = {
            "configurable": {
                "thread_id": conversation_id
            }
        }

        if confirm_action is not None:
            result = await self.graph.ainvoke(
                Command(resume=confirm_action),
                config=config,
            )
        else:
            result = await self.graph.ainvoke(
                {
                    "messages": [
                        HumanMessage(content=message)
                    ]
                },
                config=config,
            )

        interrupts = result.get("__interrupt__", [])

        if interrupts:
            interrupt_data = interrupts[0].value

            return AIChatResponse(
                answer=interrupt_data["question"],
                conversation_id=conversation_id,
                requires_confirmation=True,
            )

        return AIChatResponse(
            answer=result.get("answer", ""),
            conversation_id=conversation_id,
            requires_confirmation=result.get("requires_confirmation", False),
        )