import {useLocalStorage} from "./useLocalStorage";

export interface AppSettings {
    maxDifficulty: "easy" | "medium" | "hard";
    ingredientOverlap: "low" | "medium" | "high";
    defaultServings: number;
    calorieTarget: number;
    cuisinePreferences: string[];
    dietaryRestrictions: string[];
    pantryStaples: string[];
}

export const DEFAULT_SETTINGS: AppSettings = {
    maxDifficulty: "medium",
    ingredientOverlap: "medium",
    defaultServings: 2,
    calorieTarget: 2500,
    cuisinePreferences: [],
    dietaryRestrictions: [],
    pantryStaples: [
        "salt", "black pepper", "olive oil", "vegetable oil",
        "sugar", "all-purpose flour", "baking soda", "baking powder",
    ],
};

export function useSettings() {
    const [raw, setRaw] = useLocalStorage<AppSettings>("mealcraft:settings", DEFAULT_SETTINGS);
    // Merge with defaults so new fields are present even when loaded from old localStorage
    const settings = {...DEFAULT_SETTINGS, ...raw};
    return [settings, setRaw] as const;
}
