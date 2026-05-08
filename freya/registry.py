from __future__ import annotations

from freya.tool import Tool


class ToolRegistry:
    """In-memory registry for tools."""

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    # Backwards-compatible alias
    def register_tool(self, tool: Tool) -> None:
        self.register(tool)

    def get(self, name: str) -> Tool:
        tool = self._tools.get(name)
        if tool is None:
            raise KeyError(f"Tool '{name}' is not registered.")
        return tool

    # Backwards-compatible alias
    def get_tool(self, name: str) -> Tool:
        return self.get(name)

    def list_tools(self) -> list[str]:
        return list(self._tools.keys())

    def export_capabilities(self) -> list:
        """Introspect all registered tools and return a list of ToolCapability objects."""
        # Import here to avoid a circular import at module load time.
        from freya.planner.capabilities import ToolCapability

        caps = []
        for tool in self._tools.values():
            description = (
                (tool.__class__.__doc__ or "").strip().splitlines()[0]
                if tool.__class__.__doc__
                else tool.name
            )
            caps.append(
                ToolCapability(
                    name=tool.name,
                    description=description,
                    input_schema=tool.input_model.model_json_schema(),
                    output_schema=tool.output_model.model_json_schema(),
                )
            )
        return caps
