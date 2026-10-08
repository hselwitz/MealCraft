import {apiGet, apiPost} from "./client";
import type {PlanningWindow} from "@/hooks/usePlanningWindow";
import type {PrepPlan, GroceryList} from "@/types";
export interface WorkflowSummary {meal_count:number; servings:number; shared_ingredients:string[]; prep_ready:boolean; shop_ready:boolean; prep:PrepPlan|null}
export const workflowApi = {
    schedule: (body:{recipe_id:string; date:string; meal_type:string; servings:number}) => apiPost<{plan_id:string; slot_id:string}>("/workflow/meals",body),
    summary: (id:string,window:PlanningWindow) => apiGet<WorkflowSummary>(`/workflow/${id}/summary`, {...window}),
    prep: (id:string,window:PlanningWindow) => apiPost<PrepPlan>(`/workflow/${id}/prep`,window),
    shop: (id:string,window:PlanningWindow) => apiPost<{grocery_list_id:string; status:string}>(`/workflow/${id}/shop`,window),
    currentPrep: (id:string,window:PlanningWindow) => apiGet<PrepPlan>(`/workflow/${id}/prep`,{...window}),
    currentShop: (id:string,window:PlanningWindow) => apiGet<GroceryList>(`/workflow/${id}/shop`,{...window}),
};
