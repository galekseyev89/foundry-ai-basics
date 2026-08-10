import json
import time
from typing import Any

import requests


class MCPToolClient:
    """JSON-RPC/SSE MCP client for optional remote tools."""

    def __init__(
        self,
        server_url: str,
        api_key: str | None = None,
        tool_call_timeout_seconds: int = 10,
        max_tool_response_length: int = 4000,
        max_retries: int = 3,
        backoff_seconds: int = 1,
    ):
        self.server_url = server_url
        self.api_key = api_key
        self.tool_call_timeout_seconds = tool_call_timeout_seconds
        self.max_tool_response_length = max_tool_response_length
        self.max_retries = max_retries
        self.backoff_seconds = backoff_seconds
        self.mcp_tools: list[dict[str, Any]] = []
        self.openai_tools: list[dict[str, Any]] = []

    def list_tools(self) -> list[dict[str, Any]]:
        print(f"\n[MCP] Discovering tools from {self.server_url}...")

        payload = {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "params": {},
            "id": 1,
        }

        try:
            response = requests.post(
                self.server_url,
                headers=self._headers(),
                json=payload,
                timeout=self.tool_call_timeout_seconds,
            )
            response.raise_for_status()
            data = self._read_json_rpc_response(response)
            self.mcp_tools = data.get("result", {}).get("tools", [])
            self.openai_tools = self.convert_to_openai_tools()
        except requests.exceptions.Timeout:
            print(
                "[MCP] ERROR: Tool discovery timed out after "
                f"{self.tool_call_timeout_seconds} seconds."
            )
            self.mcp_tools = []
            self.openai_tools = []
        except requests.exceptions.RequestException as error:
            print(f"[MCP] ERROR: Tool discovery failed: {error}")
            self.mcp_tools = []
            self.openai_tools = []
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
            print(f"[MCP] ERROR: Tool discovery parsing failed: {error}")
            self.mcp_tools = []
            self.openai_tools = []

        if self.openai_tools:
            print(f"[MCP] Discovered {len(self.openai_tools)} tool(s).")
        else:
            print("[MCP] WARNING: No tools discovered.")

        return self.openai_tools

    def convert_to_openai_tools(self) -> list[dict[str, Any]]:
        openai_tools = []

        for tool in self.mcp_tools:
            openai_tools.append(
                {
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool.get("description", ""),
                        "parameters": tool.get("inputSchema", {"type": "object"}),
                    },
                }
            )

        self.openai_tools = openai_tools
        return openai_tools

    def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> str:
        print(f"\n[MCP] Calling tool '{tool_name}' with: {arguments}")

        payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": arguments},
            "id": 2,
        }

        try:
            response = requests.post(
                self.server_url,
                headers=self._headers(),
                json=payload,
                timeout=self.tool_call_timeout_seconds,
            )
            response.raise_for_status()
            data = self._read_json_rpc_response(response)

            if "error" in data:
                return f"ERROR: MCP tool call failed: {data['error']}"

            content = data.get("result", {}).get("content", [])
            text_results = [
                item.get("text", "")
                for item in content
                if item.get("type") == "text" and item.get("text")
            ]

            if not text_results:
                return json.dumps(data.get("result", {}))

            max_text_length = self.max_tool_response_length // len(text_results)
            return "\n".join(text[:max_text_length] for text in text_results)
        except requests.exceptions.Timeout:
            return (
                f"ERROR: MCP tool call to '{tool_name}' timed out after "
                f"{self.tool_call_timeout_seconds} seconds."
            )
        except requests.exceptions.RequestException as error:
            return f"ERROR: MCP tool call failed: {error}"
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
            return f"ERROR: MCP tool call parsing failed: {error}"

    def execute_tool_with_retry(
        self, tool_name: str, tool_arguments: dict[str, Any]
    ) -> str:
        last_error = None

        for attempt in range(self.max_retries):
            result = self.call_tool(tool_name, tool_arguments)
            if not result.startswith("ERROR:"):
                if attempt > 0:
                    print(f"[MCP] Retry {attempt} succeeded.")
                return result

            last_error = result
            wait_time = self.backoff_seconds * (2**attempt)
            if attempt < self.max_retries - 1:
                print(
                    f"[MCP] Attempt {attempt + 1} failed. "
                    f"Retrying in {wait_time}s..."
                )
                time.sleep(wait_time)

        return (
            f"ERROR: All {self.max_retries} attempts failed. Last error: {last_error}"
        )

    def _headers(self) -> dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }

        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
            #headers["x-api-key"] = self.api_key

        return headers

    def _read_json_rpc_response(self, response: requests.Response) -> dict[str, Any]:
        if response.headers.get("content-type", "").startswith("application/json"):
            return response.json()

        for line in response.text.splitlines():
            if line.startswith("data: "):
                json_data = line[len("data: ") :].strip().lstrip("\ufeff")
                return json.loads(json_data)

        return response.json()
