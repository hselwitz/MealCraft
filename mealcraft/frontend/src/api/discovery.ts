import {apiGet, apiPost, apiPut, apiPatch} from "./client";
import type {Recipe} from "@/types";

export type Direction = "usual" | "twist" | "new";
export interface DinnerIdea {
    title: string;
    description: string;
    familiar_connection: string;
    active_time_min: number;
    total_time_min: number;
    cleanup: string;
    extra_ingredients: string[];
    convenience_tip: string;
}
export interface DiscoveryRequest {
    request: string;
    direction: Direction;
    max_active_min: number;
    familiar_meal_id?: string;
    planning_start_date?: string;
    planning_end_date?: string;
    avoid_titles?: string[];
}
export interface RepertoireMeal {
    id: string;
    recipe_id: string | null;
    title: string;
    notes: string;
    familiar: boolean;
    saved: boolean;
    verdict: "again" | "adjust" | "no" | null;
    easy_enough: boolean | null;
    cooked_count: number;
    last_cooked_at: string | null;
}
export interface MealFeedback {
    saved?: boolean;
    cooked?: boolean;
    verdict?: RepertoireMeal["verdict"];
    easy_enough?: boolean | null;
    notes?: string;
}
export const discoveryApi = {
    ideas: (body: DiscoveryRequest) => apiPost<{ideas: DinnerIdea[]}>("/discover/ideas", body),
    recipe: (body: {idea: DinnerIdea; max_active_min: number; request: string}) => apiPost<Recipe>("/discover/recipe", body),
    repertoire: () => apiGet<RepertoireMeal[]>("/repertoire"),
    addMeal: (body: {title: string; notes: string}) => apiPost<RepertoireMeal>("/repertoire", body),
    updateMeal: (id: string, body: MealFeedback) => apiPatch<RepertoireMeal>(`/repertoire/${id}`, body),
    updateRecipe: (id: string, body: MealFeedback) => apiPut<RepertoireMeal>(`/repertoire/recipes/${id}`, body),
};
