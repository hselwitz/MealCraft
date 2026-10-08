"""OpenRouter client using structured function calls."""

import json
import logging
from pathlib import Path
from typing import AsyncGenerator

import httpx
from fastapi import Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_db
from app.models.settings import AppSettings
from app.config import settings
from app.schemas.discovery import DinnerIdeas
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

_jinja_env = Environment(loader=FileSystemLoader(str(PROMPTS_DIR)))


def _render(template_name: str, **kwargs) -> str:
    tmpl = _jinja_env.get_template(template_name)
    return tmpl.render(**kwargs)


def _extract_tool_input(response: dict, tool_name: str) -> dict:
    choices = response.get("choices", [])
    if not choices:
        raise ValueError("OpenRouter returned no completion.")
    if choices[0].get("finish_reason") == "length":
        raise ValueError("OpenRouter response was truncated even after retrying with more output space. Please try again.")
    for call in choices[0].get("message", {}).get("tool_calls", []):
        function = call.get("function", {})
        if function.get("name") == tool_name:
            return json.loads(function["arguments"])
    raise ValueError(f"OpenRouter did not return the expected '{tool_name}' function call.")


class LLMClient:
    def __init__(self, api_key: str, model: str):
        self.model = model
        self._client = httpx.AsyncClient(
            base_url="https://openrouter.ai/api/v1/",
            headers={"Authorization": f"Bearer {api_key}", "X-Title": "MealCraft"},
            timeout=180.0,
        )

    def _payload(self, *, model, max_tokens, tools, tool_choice, messages, stream=False):
        return {
            "model": model,
            "max_tokens": max_tokens,
            "tools": [{"type": "function", "function": {
                "name": tool["name"], "description": tool["description"],
                "parameters": tool["input_schema"],
            }} for tool in tools],
            # Some tool-capable models cannot route forced/named tool choices.
            # Prompts request the single available tool; parsing still requires it.
            "tool_choice": "auto",
            "messages": messages,
            "provider": {"require_parameters": True},
            "stream": stream,
        }

    @staticmethod
    def _check_response(response):
        if response.is_error:
            # Do not expose upstream response bodies or credentials in user-facing errors.
            messages = {
                401: "OpenRouter rejected the API key. Update it in Settings.",
                402: "OpenRouter credits are insufficient. Check your OpenRouter account.",
                404: "OpenRouter found no compatible endpoint. Check the model ID and your OpenRouter provider settings.",
                429: "OpenRouter rate limit reached. Try again shortly.",
            }
            raise ValueError(messages.get(response.status_code,
                f"OpenRouter request failed (HTTP {response.status_code}). Check the model and try again."))

    async def _create(self, retry_truncated=True, **kwargs):
        # Restart a cut-off completion once; never parse or save partial tool JSON.
        for attempt in range(2 if retry_truncated else 1):
            response = await self._client.post("chat/completions", json=self._payload(**kwargs))
            self._check_response(response)
            data = response.json()
            if "error" in data:
                raise ValueError("OpenRouter could not complete the request. Check the model and try again.")
            choices = data.get("choices", [])
            if retry_truncated and attempt == 0 and choices and choices[0].get("finish_reason") == "length":
                kwargs["max_tokens"] = min(kwargs["max_tokens"] * 2, 32768)
                logger.warning("OpenRouter completion truncated; retrying with max_tokens=%s", kwargs["max_tokens"])
                continue
            return data

    async def suggest_dinners(self, request, repertoire, user_settings, selected=None):
        prompt = _render("discovery.j2", request=request, repertoire=repertoire,
                         settings=user_settings, selected=selected)
        tool = {"name": "suggest_dinners", "description": "Suggest three convenient, distinct dinners.",
                "input_schema": DinnerIdeas.model_json_schema()}
        response = await self._create(model=self.model, max_tokens=3000, tools=[tool],
                                      tool_choice={"name": "suggest_dinners"},
                                      messages=[{"role": "user", "content": prompt}])
        ideas = DinnerIdeas.model_validate(_extract_tool_input(response, "suggest_dinners"))
        if any(idea.active_time_min > request.max_active_min for idea in ideas.ideas):
            raise ValueError("Ideas exceeded your hands-on budget. Please try again.")
        return ideas

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
        response = await self._create(
            model=self.model,
            max_tokens=8192,
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
            prefer_store_bought=constraints.get("prefer_store_bought", True),
        )
        response = await self._create(
            model=self.model,
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
        payload = self._payload(
            model=self.model, max_tokens=8192, tools=[GENERATE_RECIPE_TOOL],
            tool_choice={"name": "generate_recipe"},
            messages=[{"role": "user", "content": prompt}], stream=True,
        )
        names = {}
        arguments = {}
        truncated = False
        async with self._client.stream("POST", "chat/completions", json=payload) as response:
            if response.is_error:
                await response.aread()
                self._check_response(response)
            async for line in response.aiter_lines():
                if not line.startswith("data:"):
                    continue
                raw = line[5:].strip()
                if raw == "[DONE]":
                    break
                event = json.loads(raw)
                if "error" in event:
                    raise ValueError("OpenRouter interrupted recipe generation. Try again.")
                for choice in event.get("choices", []):
                    truncated |= choice.get("finish_reason") == "length"
                    for call in choice.get("delta", {}).get("tool_calls", []):
                        index = call.get("index", 0)
                        function = call.get("function", {})
                        if function.get("name"):
                            names[index] = function["name"]
                        partial = function.get("arguments", "")
                        arguments[index] = arguments.get(index, "") + partial
                        if partial:
                            yield f"data: {json.dumps({'partial': partial})}\n\n"
        if truncated:
            response = await self._create(
                retry_truncated=False, model=self.model, max_tokens=16384, tools=[GENERATE_RECIPE_TOOL],
                tool_choice={"name": "generate_recipe"},
                messages=[{"role": "user", "content": prompt}],
            )
            recipe = RecipeOutput.model_validate(_extract_tool_input(response, "generate_recipe"))
            yield f"data: {json.dumps({'complete': True, 'recipe': recipe.model_dump()})}\n\n"
            return
        accumulated = next((arguments[i] for i, name in names.items()
                            if name == "generate_recipe"), "")

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
            prefer_store_bought=preferences.get("prefer_store_bought", True),
        )
        response = await self._create(
            model=self.model,
            max_tokens=4096,
            tools=[CREATE_WEEKLY_PLAN_TOOL],
            tool_choice={"type": "tool", "name": "create_weekly_plan"},
            messages=[{"role": "user", "content": prompt}],
        )
        data = _extract_tool_input(response, "create_weekly_plan")
        return WeeklyPlanOutput.model_validate(data)

    async def coordinate_meals(self, meals, preferences, window):
        from app.schemas.workflow import CoordinatedPrep
        prompt = _render("coordinated_prep.j2", meals=meals, preferences=preferences, window=window)
        tool = {"name": "coordinate_meals", "description": "Coordinate selected meals into a batch prep session and complete raw shopping requirements.",
                "input_schema": CoordinatedPrep.model_json_schema()}
        response = await self._create(model=self.model, max_tokens=8096, tools=[tool],
                                      tool_choice={"name": "coordinate_meals"},
                                      messages=[{"role": "user", "content": prompt}])
        result = CoordinatedPrep.model_validate(_extract_tool_input(response, "coordinate_meals"))
        if not result.tasks or not result.grocery_ingredients:
            raise ValueError("The prep session was incomplete. Please try again.")
        if {m.recipe_id for m in result.meal_finishes} != {m["recipe_id"] for m in meals}:
            raise ValueError("The prep session did not cover every selected recipe. Please try again.")
        names = [task.task_name for task in result.tasks]
        if len(names) != len(set(names)) or any(dep not in names for task in result.tasks for dep in task.depends_on):
            raise ValueError("The prep tasks had invalid dependencies. Please try again.")
        return result

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
        response = await self._create(
            model=self.model,
            max_tokens=3000,
            tools=[OPTIMIZE_PREP_PLAN_TOOL],
            tool_choice={"type": "tool", "name": "optimize_prep_plan"},
            messages=[{"role": "user", "content": prompt}],
        )
        data = _extract_tool_input(response, "optimize_prep_plan")
        return PrepPlanOutput.model_validate(data)

    async def generate_grocery_list(
        self, ingredients: list, pantry: list, leftovers: list, ingredient_overlap: str = "medium",
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
        )
        messages = [{"role": "user", "content": prompt}]
        for attempt in range(2):
            response = await self._create(
                model=self.model,
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
                        {"role": "assistant", "content": json.dumps(data)},
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
        response = await self._create(
            model=self.model,
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


async def get_llm_client(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AppSettings).where(AppSettings.id == "default"))
    row = result.scalar_one_or_none()
    data = row.data if row else {}
    api_key = data.get("openRouterApiKey") or settings.openrouter_api_key
    model = data.get("openRouterModel") or settings.openrouter_model
    if not api_key:
        raise HTTPException(status_code=503, detail="Add your OpenRouter API key in Settings to generate meals.")
    client = LLMClient(api_key=api_key, model=model)
    try:
        yield client
    finally:
        await client._client.aclose()
