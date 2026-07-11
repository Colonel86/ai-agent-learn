import logging

from pydantic import Field

from nat.plugin_api import Builder
from nat.plugin_api import FunctionBaseConfig
from nat.plugin_api import FunctionInfo
from nat.plugin_api import LLMFrameworkEnum
from nat.plugin_api import register_function

logger = logging.getLogger(__name__)


class ClimateAssistantFunctionConfig(FunctionBaseConfig, name="climate_assistant"):
    """
    NAT function template. Please update the description.
    """
    prefix: str = Field(default="Echo:", description="Prefix to add before the echoed text.")


@register_function(config_type=ClimateAssistantFunctionConfig, framework_wrappers=[LLMFrameworkEnum.LANGCHAIN])
async def climate_assistant_function(config: ClimateAssistantFunctionConfig, builder: Builder):
    """
    Registers a function (addressable via `climate_assistant` in the configuration).
    This registration ensures a static mapping of the function type, `climate_assistant`, to the `ClimateAssistantFunctionConfig` configuration object.

    Args:
        config (ClimateAssistantFunctionConfig): The configuration for the function.
        builder (Builder): The builder object.

    Returns:
        FunctionInfo: The function info object for the function.
    """

    # Define the function that will be registered.
    async def _echo(text: str) -> str:
        """
        Takes a text input and echoes back with a pre-defined prefix.

        Args:
            text (str): The text to echo back.

        Returns:
            str: The text with the prefix.
        """
        return f"{config.prefix} {text}"

    # The callable is wrapped in a FunctionInfo object.
    # The description parameter is used to describe the function.
    yield FunctionInfo.from_fn(_echo, description=_echo.__doc__)
