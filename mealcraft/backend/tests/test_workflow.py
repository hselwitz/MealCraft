import unittest
from datetime import date
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.db import Base, get_db
from app.llm.client import get_llm_client
from app.llm.schemas import GroceryListOutput
from app.schemas.workflow import CoordinatedPrep
from app.models.recipe import Recipe, RecipeStep
from app.models.ingredient import Ingredient, RecipeIngredient
from app.models.meal_plan import MealPlan, MealSlot
from app.routers.workflow import router
from app.routers.plans import router as plans_router
from app.routers.grocery import router as grocery_router
from app.services.planner import PlannerService

WINDOW = {"start_date": "2030-01-10", "end_date": "2030-01-12"}

class WorkflowLLM:
    async def coordinate_meals(self, meals, prefs, window):
        self.meals = meals
        totals = {}
        for meal in meals:
            for ingredient in meal['ingredients']:
                key = (ingredient['ingredient_name'], ingredient['unit'])
                totals[key] = totals.get(key, 0) + ingredient['quantity']
        return CoordinatedPrep.model_validate({
            "tasks": [{"task_name": "Cook rice for all portions", "duration_min": 5, "is_active": True}],
            "total_active_min": 5, "total_passive_min": 40, "session_elapsed_min": 45,
            "shared_components": ["rice"], "recommended_sessions": ["One prep session"],
            "meal_finishes": [{"recipe_id": meal['recipe_id'], "title": meal['title'], "instructions": "Reheat and assemble", "active_min": 3} for i, meal in enumerate(meals) if meal['recipe_id'] not in {m['recipe_id'] for m in meals[:i]}],
            "grocery_ingredients": [{"ingredient_name": name, "quantity": quantity, "unit": unit} for (name, unit),quantity in totals.items()],
        })
    async def generate_grocery_list(self, ingredients, **kwargs):
        self.ingredients = ingredients
        return GroceryListOutput.model_validate({"items": [{**i,"store_section":"pantry"} for i in ingredients]})

class WorkflowTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.engine=create_async_engine('sqlite+aiosqlite:///:memory:')
        async with self.engine.begin() as connection: await connection.run_sync(Base.metadata.create_all)
        self.sessions=async_sessionmaker(self.engine,expire_on_commit=False)
        async with self.sessions() as session:
            rice=Ingredient(id='rice',canonical_name='rice'); chicken=Ingredient(id='chicken',canonical_name='chicken breast')
            session.add_all([rice,chicken])
            for id in ('r1','r2'):
                session.add(Recipe(id=id,title=id,description='Complete recipe',prep_time_min=5,cook_time_min=30,total_time_min=35,difficulty='easy',servings=2,tags=[]))
                session.add(RecipeIngredient(recipe_id=id,ingredient_id='rice',quantity=2,unit='cups',is_optional=False))
                session.add(RecipeStep(recipe_id=id,step_number=1,instruction='Cook the ingredients',duration_min=5,is_active=True))
            session.add(RecipeIngredient(recipe_id='r1',ingredient_id='chicken',quantity=2,unit='pieces',is_optional=False))
            await session.commit()
        async def database():
            async with self.sessions() as session:
                yield session
                await session.commit()
        self.llm=WorkflowLLM()
        async def llm(): yield self.llm
        app=FastAPI();app.include_router(router,prefix='/api');app.include_router(plans_router,prefix='/api');app.include_router(grocery_router,prefix='/api')
        app.dependency_overrides[get_db]=database;app.dependency_overrides[get_llm_client]=llm
        self.http=TestClient(app)
        for recipe, day, servings in [('r1',10,4),('r1',11,2),('r2',12,3),('r2',20,8)]:
            result=self.http.post('/api/workflow/meals',json={'recipe_id':recipe,'date':f'2030-01-{day}','servings':servings})
            self.assertEqual(result.status_code,200,result.text);self.plan_id=result.json()['plan_id']
    async def asyncTearDown(self):
        self.http.close();await self.engine.dispose()
    def url(self,path): return f'/api/workflow/{self.plan_id}/{path}'

    async def test_selected_portions_drive_shopping_and_prep(self):
        summary=self.http.get(self.url('summary'),params=WINDOW).json()
        self.assertEqual(summary['meal_count'],3);self.assertEqual(summary['servings'],9)
        self.assertIn('rice',summary['shared_ingredients'])
        self.assertEqual(self.http.post(self.url('prep'),json=WINDOW).status_code,200)
        self.assertEqual([m['servings'] for m in self.llm.meals],[4,2,3])
        self.assertEqual(sum(i['quantity'] for m in self.llm.meals for i in m['ingredients'] if i['ingredient_name']=='rice'),9)
        self.assertEqual(self.http.post(self.url('shop'),json=WINDOW).status_code,200)
        self.assertEqual(next(i['quantity'] for i in self.llm.ingredients if i['ingredient_name']=='rice'),9)
        summary=self.http.get(self.url('summary'),params=WINDOW).json()
        self.assertTrue(summary['shop_ready']);self.assertTrue(summary['prep_ready'])
        self.assertEqual(len(summary['prep']['meal_finishes']),2)

    async def test_changed_portions_flag_both_outputs_and_uncheck_increased_quantities(self):
        self.http.post(self.url('prep'),json=WINDOW);self.http.post(self.url('shop'),json=WINDOW)
        groceries=self.http.get(self.url('shop'),params=WINDOW).json()
        for item in groceries['items']:
            self.http.patch(f'/api/grocery-lists/{groceries["id"]}/items/{item["id"]}',json={'checked':True})
        self.http.post('/api/workflow/meals',json={'recipe_id':'r2','date':'2030-01-12','servings':5})
        self.assertTrue(self.http.get(self.url('shop'),params=WINDOW).json()['stale'])
        self.assertTrue(self.http.get(self.url('prep'),params=WINDOW).json()['stale'])
        self.http.post(self.url('shop'),json=WINDOW)
        items=self.http.get(self.url('shop'),params=WINDOW).json()['items']
        self.assertFalse(next(i['checked'] for i in items if i['ingredient_name']=='rice'))
        self.assertTrue(next(i['checked'] for i in items if i['ingredient_name']=='chicken breast'))

    async def test_assembly_requires_current_prep_and_avoids_double_counting(self):
        async with self.sessions() as session:
            recipe=await session.get(Recipe,'r1');recipe.tags=['batch-assembly'];await session.commit()
        self.assertEqual(self.http.post(self.url('shop'),json=WINDOW).status_code,400)
        self.http.post(self.url('prep'),json=WINDOW)
        self.assertEqual(self.http.post(self.url('shop'),json=WINDOW).status_code,200)
        self.assertEqual(next(i['quantity'] for i in self.llm.ingredients if i['ingredient_name']=='rice'),9)
        self.http.post(self.url('prep'),json=WINDOW)
        self.assertTrue(self.http.get(self.url('shop'),params=WINDOW).json()['stale'])

    async def test_existing_slot_not_overwritten_and_empty_window_rejected(self):
        result=self.http.post('/api/workflow/meals',json={'recipe_id':'r2','date':'2030-01-10','servings':3})
        self.assertEqual(result.status_code,409)
        self.assertEqual(self.http.post(self.url('prep'),json={'start_date':'2030-02-01','end_date':'2030-02-07'}).status_code,400)
        self.assertEqual(self.http.get(self.url('summary'),params={'start_date':'2030-02-10','end_date':'2030-02-01'}).status_code,422)
        async with self.sessions() as session:
            slot=await session.scalar(select(MealSlot).where(MealSlot.date==date(2030,1,10)))
            self.assertEqual(slot.recipe_id,'r1');self.assertEqual(float(slot.servings),4)

    async def test_generation_preserves_chosen_recipes(self):
        async with self.sessions() as session:
            plan=await session.get(MealPlan,self.plan_id)
            messages=[message async for message in PlannerService(session,self.llm).generate_plan(plan,{}, {}, [], [])]
            self.assertEqual(messages,['__DONE__'])
            slots=(await session.execute(select(MealSlot))).scalars().all()
            self.assertTrue(all(slot.recipe_id for slot in slots))
