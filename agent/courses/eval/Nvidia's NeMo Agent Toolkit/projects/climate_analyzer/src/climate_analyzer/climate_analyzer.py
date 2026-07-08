"""NAT tool registrations for the five climate tools (course L3 Part 2).

每个工具三件套:Pydantic 输入 schema + Config 类(YAML 里的 _type)+ 注册装饰器。
真正干活的仍是 climate_tools.py 里的普通函数。
"""
import logging

from pydantic import BaseModel, Field

from nat.plugin_api import Builder
from nat.plugin_api import FunctionBaseConfig
from nat.plugin_api import FunctionInfo
from nat.plugin_api import LLMFrameworkEnum
from nat.plugin_api import register_function

from .climate_tools import (
    load_climate_data,
    calculate_statistics,
    filter_by_country,
    find_extreme_years,
    create_visualization,
    list_countries,
    station_statistics,
)

logger = logging.getLogger(__name__)


# ---------- calculate_statistics ----------

class CalculateStatsInput(BaseModel):
    country: str = Field(
        default="",
        description="Country name to filter by (e.g., 'United States', 'France'). "
                    "Leave empty for global statistics.")
    start_year: int = Field(default=0, description="First year to include, 0 for no limit.")
    end_year: int = Field(default=0, description="Last year to include, 0 for no limit.")


class CalculateStatisticsConfig(FunctionBaseConfig, name="calculate_statistics"):
    """Configuration for calculating climate statistics."""
    pass


@register_function(config_type=CalculateStatisticsConfig)
async def calculate_statistics_tool(config: CalculateStatisticsConfig, builder: Builder):
    df = load_climate_data()

    async def _wrapper(params: CalculateStatsInput) -> str:
        return calculate_statistics(df,
                                    None if params.country == "" else params.country,
                                    params.start_year or None,
                                    params.end_year or None)

    yield FunctionInfo.from_fn(
        _wrapper,
        input_schema=CalculateStatsInput,
        description=("Calculate temperature statistics globally or for a specific country. "
                     "Returns JSON with: mean_temperature (°C), min_temperature (°C), "
                     "max_temperature (°C), std_deviation (°C), num_records (count), "
                     "trend_per_decade (°C/decade), years_analyzed (e.g. '1950-2025'), "
                     "and country (if specified)."))


# ---------- filter_by_country ----------

class FilterByCountryInput(BaseModel):
    country: str = Field(description="Exact country name, e.g. 'France'.")


class FilterByCountryConfig(FunctionBaseConfig, name="filter_by_country"):
    """Configuration for filtering climate data by country."""
    pass


@register_function(config_type=FilterByCountryConfig)
async def filter_by_country_tool(config: FilterByCountryConfig, builder: Builder):
    df = load_climate_data()

    async def _wrapper(country: str) -> str:
        return filter_by_country(df, country)

    yield FunctionInfo.from_fn(
        _wrapper,
        input_schema=FilterByCountryInput,
        description=("Get dataset coverage for one country: number of records, number of "
                     "weather stations (num_stations), and years covered. Returns JSON. "
                     "Use this for questions about stations or data availability."))


# ---------- find_extreme_years ----------

class FindExtremeYearsInput(BaseModel):
    country: str = Field(
        default="",
        description="Country name, leave empty for global extremes.")
    top_n: int = Field(default=5, description="How many years to return per list.")


class FindExtremeYearsConfig(FunctionBaseConfig, name="find_extreme_years"):
    """Configuration for finding extreme years."""
    pass


@register_function(config_type=FindExtremeYearsConfig)
async def find_extreme_years_tool(config: FindExtremeYearsConfig, builder: Builder):
    df = load_climate_data()

    async def _wrapper(params: FindExtremeYearsInput) -> str:
        country = None if params.country == "" else params.country
        return find_extreme_years(df, country, params.top_n)

    yield FunctionInfo.from_fn(
        _wrapper,
        input_schema=FindExtremeYearsInput,
        description=("Find the warmest and coldest years on record, globally or for a "
                     "specific country. Returns JSON with ranked warmest_years and "
                     "coldest_years lists of {year, temperature_anomaly}."))


# ---------- create_visualization ----------

class CreateVisualizationInput(BaseModel):
    plot_type: str = Field(
        default="annual_trend",
        description="'annual_trend' for the global temperature line chart, or "
                    "'country_trends' for a bar chart of the top-5 fastest-warming countries.")
    save_path: str = Field(default="climate_plot.png",
                           description="PNG file path to save the chart to.")


class CreateVisualizationConfig(FunctionBaseConfig, name="create_visualization"):
    """Configuration for creating visualizations."""
    pass


@register_function(config_type=CreateVisualizationConfig)
async def create_visualization_tool(config: CreateVisualizationConfig, builder: Builder):
    df = load_climate_data()

    async def _wrapper(params: CreateVisualizationInput) -> str:
        return create_visualization(df, params.plot_type, params.save_path)

    yield FunctionInfo.from_fn(
        _wrapper,
        input_schema=CreateVisualizationInput,
        description=("Create a chart and save it as a PNG file. plot_type 'annual_trend' "
                     "plots global mean anomaly per year; 'country_trends' plots warming "
                     "trend per decade for the 5 fastest-warming countries. "
                     "Returns JSON confirming the saved file path."))


# ---------- list_countries ----------

class ListCountriesInput(BaseModel):
    pass


class ListCountriesConfig(FunctionBaseConfig, name="list_countries"):
    """Configuration for listing available countries."""
    pass


@register_function(config_type=ListCountriesConfig)
async def list_countries_tool(config: ListCountriesConfig, builder: Builder):
    df = load_climate_data()

    async def _wrapper(params: ListCountriesInput) -> str:
        return list_countries(df)

    yield FunctionInfo.from_fn(
        _wrapper,
        input_schema=ListCountriesInput,
        description="List all countries available in the climate dataset. Returns a JSON array.")


# ---------- station_statistics(L4 观测驱动补的工具)----------

class StationStatisticsInput(BaseModel):
    pass


class StationStatisticsConfig(FunctionBaseConfig, name="station_statistics"):
    """Configuration for weather station statistics."""
    pass


@register_function(config_type=StationStatisticsConfig)
async def station_statistics_tool(config: StationStatisticsConfig, builder: Builder):
    df = load_climate_data()

    async def _wrapper(params: StationStatisticsInput) -> str:
        return station_statistics(df)

    yield FunctionInfo.from_fn(
        _wrapper,
        input_schema=StationStatisticsInput,
        description=("Get weather station statistics across all countries: total_stations, "
                     "countries_with_most_stations (top 5 ranked), and stations_per_country "
                     "breakdown. Use this for any question about weather station counts."))


# ---------- calculator_agent(L5:LangGraph agent 包成 NAT 工具)----------

class CalculatorInput(BaseModel):
    question: str = Field(description="A self-contained math question including all needed numbers.")


class CalculatorAgentConfig(FunctionBaseConfig, name="calculator_agent"):
    """Configuration for the LangGraph calculator agent."""
    pass


@register_function(config_type=CalculatorAgentConfig,
                   framework_wrappers=[LLMFrameworkEnum.LANGCHAIN])  # 变化①:声明被包的是 LangChain 系 agent
async def calculator_agent_tool(config: CalculatorAgentConfig, builder: Builder):
    from .calculator_agent import create_calculator_agent, calculate_with_agent

    # 变化②:LLM Lifting —— 不在 agent 里硬编码 LLM,向 builder 要 YAML 里定义的 calculator_llm
    llm = await builder.get_llm("calculator_llm", wrapper_type=LLMFrameworkEnum.LANGCHAIN)
    agent = create_calculator_agent(llm)

    async def _wrapper(params: CalculatorInput) -> str:
        return await calculate_with_agent(params.question, agent)

    yield FunctionInfo.from_fn(
        _wrapper,
        input_schema=CalculatorInput,
        description=("Calculates compound growth rates, percentage changes, weighted averages, "
                     "projections, and multi-step calculations. Shows all calculation steps. "
                     "Does not have access to climate data. If calculations need to be performed "
                     "on climate data, be sure to acquire that data with other tools first and "
                     "include the numbers in the input question to this tool."))
