import {useLocalStorage} from "./useLocalStorage";

export interface AppSettings {
    maxDifficulty: "easy" | "medium" | "hard";
    ingredientOverlap: "low" | "medium" | "high";
    defaultServings: number;
    calorieTarget: number;
    cuisinePreferences: string[];
    dietaryRestrictions: string[];
}

export const DEFAULT_SETTINGS: AppSettings = {
    maxDifficulty: "medium",
    ingredientOverlap: "medium",
    defaultServings: 2,
    calorieTarget: 2500,
    cuisinePreferences: [],
    dietaryRestrictions: [],
};

export function useSettings() {
    return useLocalStorage<AppSettings>("mealcraft:settings", DEFAULT_SETTINGS);
}
