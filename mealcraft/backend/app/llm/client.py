"""LLM client wrapping Anthropic API with tool_use pattern."""

import json
import logging
from pathlib import Path
from typing import AsyncGenerator

import anthropic
from app.config import settings
from app.llm.schemas import (
    RecipeOutput,
    WeeklyPlanOutput,
    PrepPlanOutput,
    GroceryListOutput,
    LeftoverSuggestionOutput,
)
from app.llm.tools import (
    CREATE_WEEKLY_PLAN_TOOL,
    GENERATE_RECIPE_TOOL,
    OPTIMIZE_PREP_PLAN_TOOL,
    GENERATE_GROCERY_LIST_TOOL,
    SUGGEST_LEFTOVER_USE_TOOL,
)
from jinja2 import Environment, FileSystemLoader
from rapidfuzz import fuzz, process

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).parent / "prompts"
MODEL = "claude-sonnet-4-20250514"

_jinja_env = Environment(loader=FileSystemLoader(str(PROMPTS_DIR)))


def _render(template_name: str, **kwargs) -> str:
    tmpl = _jinja_env.get_template(template_name)
    return tmpl.render(**kwargs)


def _extract_tool_input(response: anthropic.types.Message, tool_name: str) -> dict:
    for block in response.content:
        if block.type == "tool_use" and block.name == tool_name:
            return block.input
    raise ValueError(f"Tool '{tool_name}' not found in response. Content: {response.content}")


class LLMClient:
    def __init__(self):
        self._client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    async def generate_recipe(self, concept: str, constraints: dict) -> RecipeOutput:
        _excluded = {"target_servings", "max_difficulty", "dietary_restrictions", "calorie_target"}
        prompt = _render(
            "recipe.j2",
            concept=concept,
            target_servings=constraints.get("target_servings", 4),
            max_difficulty=constraints.get("max_difficulty", "medium"),
            dietary_restrictions=constraints.get("dietary_restrictions", []),
            constraints={k: v for k, v in constraints.items() if k not in _excluded},
            calorie_target=constraints.get("calorie_target"),
        )
        response = await self._client.messages.create(
            model=MODEL,
            max_tokens=4096,
            tools=[GENERATE_RECIPE_TOOL],
            tool_choice={"type": "tool", "name": "generate_recipe"},
            messages=[{"role": "user", "content": prompt}],
        )
        data = _extract_tool_input(response, "generate_recipe")
        return RecipeOutput.model_validate(data)

    async def generate_assembly_recipe(self, concept: str, constraints: dict, batch_components: list[str]) -> RecipeOutput:
        """Generate an assembly-only serving guide using pre-cooked batch components."""
        prompt = _render(
            "assembly.j2",
            concept=concept,
            target_servings=constraints.get("target_servings", 2),
            dietary_restrictions=constraints.get("dietary_restrictions", []),
            calorie_target=constraints.get("calorie_target"),
            batch_components=batch_components,
        )
        response = await self._client.messages.create(
            model=MODEL,
            max_tokens=2048,
            tools=[GENERATE_RECIPE_TOOL],
            tool_choice={"type": "tool", "name": "generate_recipe"},
            messages=[{"role": "user", "content": prompt}],
        )
        data = _extract_tool_input(response, "generate_recipe")

        # Hard enforcement — not left to LLM judgment
        data["cook_time_min"] = min(data.get("cook_time_min", 0), 3)
        data["difficulty"] = "easy"
        tags = data.get("tags", [])
        if "batch-assembly" not in tags:
            tags.append("batch-assembly")
        data["tags"] = tags

        return RecipeOutput.model_validate(data)

    async def generate_recipe_stream(
        self, concept: str, constraints: dict
    ) -> AsyncGenerator[str, None]:
        """Stream recipe generation as SSE events."""
        prompt = _render(
            "recipe.j2",
            concept=concept,
            target_servings=constraints.get("target_servings", 4),
            max_difficulty=constraints.get("max_difficulty", "medium"),
            dietary_restrictions=constraints.get("dietary_restrictions", []),
            constraints={},
            calorie_target=constraints.get("calorie_target"),
        )

        accumulated = ""
        async with self._client.messages.stream(
            model=MODEL,
            max_tokens=4096,
            tools=[GENERATE_RECIPE_TOOL],
            tool_choice={"type": "tool", "name": "generate_recipe"},
            messages=[{"role": "user", "content": prompt}],
        ) as stream:
            async for event in stream:
                if hasattr(event, "type"):
                    if event.type == "content_block_delta":
                        delta = event.delta
                        if hasattr(delta, "partial_json"):
                            accumulated += delta.partial_json
                            yield f"data: {json.dumps({'partial': delta.partial_json})}\n\n"
                    elif event.type == "message_stop":
                        pass

        # Final: parse and emit complete recipe
        try:
            data = json.loads(accumulated)
            recipe = RecipeOutput.model_validate(data)
            yield f"data: {json.dumps({'complete': True, 'recipe': recipe.model_dump()})}\n\n"
        except Exception as e:
            logger.error(f"Failed to parse streamed recipe: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    async def generate_weekly_plan(
        self,
        preferences: dict,
        schedule: dict,
        leftovers: list,
        pantry: list,
    ) -> WeeklyPlanOutput:
        prompt = _render(
            "weekly_plan.j2",
            start_date=preferences.get("start_date", ""),
            end_date=preferences.get("end_date", ""),
            calorie_target=preferences.get("calorie_target", 2500),
            max_difficulty=preferences.get("max_difficulty", "medium"),
            ingredient_overlap=preferences.get("ingredient_overlap", "medium"),
            household_size=preferences.get("household_size", 2),
            dietary_restrictions=preferences.get("dietary_restrictions", []),
            cuisine_preferences=preferences.get("cuisine_preferences", []),
            schedule_notes=schedule,
            available_leftovers=leftovers,
            pantry_staples=pantry,
            slots_to_fill=preferences.get("slots_to_fill", []),
            meal_prep_focus=preferences.get("meal_prep_focus", True),
        )
        response = await self._client.messages.create(
            model=MODEL,
            max_tokens=4096,
            tools=[CREATE_WEEKLY_PLAN_TOOL],
            tool_choice={"type": "tool", "name": "create_weekly_plan"},
            messages=[{"role": "user", "content": prompt}],
        )
        data = _extract_tool_input(response, "create_weekly_plan")
        return WeeklyPlanOutput.model_validate(data)

    async def optimize_prep_plan(
        self,
        batch_components: list[str],
        servings: int,
        first_meal_date: str,
        last_meal_date: str,
        dietary_restrictions: list[str] | None = None,
    ) -> PrepPlanOutput:
        from datetime import date as _date, datetime as _datetime
        today = _date.today()

        def _weekday(d: str) -> str:
            return _datetime.strptime(d, "%Y-%m-%d").strftime("%A")

        prompt = _render(
            "prep_plan.j2",
            batch_components=batch_components,
            servings=servings,
            dietary_restrictions=dietary_restrictions or [],
            today=str(today),
            today_weekday=today.strftime("%A"),
            first_meal_date=first_meal_date,
            first_meal_weekday=_weekday(first_meal_date),
            last_meal_date=last_meal_date,
            last_meal_weekday=_weekday(last_meal_date),
        )
        response = await self._client.messages.create(
            model=MODEL,
            max_tokens=3000,
            tools=[OPTIMIZE_PREP_PLAN_TOOL],
            tool_choice={"type": "tool", "name": "optimize_prep_plan"},
            messages=[{"role": "user", "content": prompt}],
        )
        data = _extract_tool_input(response, "optimize_prep_plan")
        return PrepPlanOutput.model_validate(data)

    async def generate_grocery_list(
        self, ingredients: list, pantry: list, leftovers: list, ingredient_overlap: str = "medium",
        batch_components: list[str] | None = None, batch_servings: int = 2,
    ) -> GroceryListOutput:
        # Strip heavy fields before sending to reduce prompt size
        slim_ingredients = [
            {"ingredient_name": i["ingredient_name"], "quantity": i["quantity"], "unit": i["unit"]}
            for i in ingredients
        ]
        prompt = _render(
            "grocery.j2",
            ingredients=slim_ingredients,
            pantry_items=pantry,
            leftover_inventory=leftovers,
            ingredient_overlap=ingredient_overlap,
            batch_components=batch_components or [],
            batch_servings=batch_servings,
        )
        messages = [{"role": "user", "content": prompt}]
        for attempt in range(2):
            response = await self._client.messages.create(
                model=MODEL,
                max_tokens=8096,
                tools=[GENERATE_GROCERY_LIST_TOOL],
                tool_choice={"type": "tool", "name": "generate_grocery_list"},
                messages=messages,
            )
            data = _extract_tool_input(response, "generate_grocery_list")
            try:
                return GroceryListOutput.model_validate(data)
            except Exception as e:
                if attempt == 0:
                    logger.warning(f"Grocery list validation failed, retrying: {e}")
                    messages += [
                        {"role": "assistant", "content": response.content},
                        {
                            "role": "user",
                            "content": f"Validation error: {e}. Please retry with the correct schema.",
                        },
                    ]
                else:
                    raise

    async def suggest_leftover_use(
        self, leftovers: list, empty_slots: list
    ) -> LeftoverSuggestionOutput:
        leftover_desc = "\n".join(
            f"- {lv.get('recipe_title', 'Unknown')}: {lv.get('remaining_servings', 0)} servings, "
            f"expires {lv.get('expiry_date', 'unknown')}"
            for lv in leftovers
        )
        slot_desc = (
            "\n".join(f"- {s}" for s in empty_slots)
            if empty_slots
            else "- No specific slots, general suggestions welcome"
        )

        prompt = (
            f"I have the following leftovers:\n{leftover_desc}\n\n"
            f"Available meal slots to fill:\n{slot_desc}\n\n"
            "Please suggest creative, practical ways to use these leftovers. "
            "Consider combining multiple leftovers, repurposing them into new dishes, "
            "and prioritizing items expiring soonest. "
            "Use the `suggest_leftover_use` tool to return your suggestions."
        )
        response = await self._client.messages.create(
            model=MODEL,
            max_tokens=1000,
            tools=[SUGGEST_LEFTOVER_USE_TOOL],
            tool_choice={"type": "tool", "name": "suggest_leftover_use"},
            messages=[{"role": "user", "content": prompt}],
        )
        data = _extract_tool_input(response, "suggest_leftover_use")
        return LeftoverSuggestionOutput.model_validate(data)

    async def canonicalize_ingredient(self, name: str, existing: list[str]) -> str:
        """Canonicalize ingredient name using rapidfuzz first, LLM fallback."""
        if not existing:
            return name.strip().lower()

        # Try rapidfuzz first (threshold 90)
        result = process.extractOne(name, existing, scorer=fuzz.WRatio, score_cutoff=90)
        if result:
            matched_name, score, _ = result
            logger.debug(f"Rapidfuzz match: '{name}' -> '{matched_name}' (score={score})")
            return matched_name

        # No match — normalize locally: lowercase, strip prep notes after comma/parens
        import re

        canonical = name.strip().lower()
        canonical = re.sub(r"\s*[\(,].*", "", canonical).strip()
        logger.debug(f"Local canonicalization: '{name}' -> '{canonical}'")
        return canonical


# Singleton
_llm_client: LLMClient | None = None


def get_llm_client() -> LLMClient:
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client
