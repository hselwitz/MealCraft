// ─── Plan & Slots ────────────────────────────────────────────────────────────

export type PlanStatus = "draft" | "active" | "archived";
export type MealType = "breakfast" | "lunch" | "dinner" | "snack";
export type SlotStatus = "planned" | "cooked" | "skipped" | "eating_out";

export interface RecipeSummary {
    id: string;
    title: string;
    description: string;
    prep_time_min: number;
    cook_time_min: number;
    total_time_min: number;
    difficulty: "easy" | "medium" | "hard";
    servings: number;
    calories_per_serving: number | null;
    tags: string[];
}

export interface MealSlot {
    id: string;
    meal_plan_id: string;
    date: string;
    meal_type: MealType;
    status: SlotStatus;
    recipe_id: string | null;
    servings: number;
    notes: string | null;
    recipe: RecipeSummary | null;
}

export interface MealPlan {
    id: string;
    name: string;
    start_date: string;
    end_date: string;
    calorie_target: number | null;
    status: PlanStatus;
    created_at: string;
    slots: MealSlot[];
}

export interface MealPlanListItem {
    id: string;
    name: string;
    start_date: string;
    end_date: string;
    status: PlanStatus;
    created_at: string;
}

export interface SlotConfig {
    date: string;
    meal_type: MealType;
    status?: SlotStatus;
}

export interface CreatePlanRequest {
    name: string;
    start_date: string;
    end_date: string;
    calorie_target?: number;
    slots_config: SlotConfig[];
}

export interface UpdateSlotRequest {
    status?: SlotStatus;
    recipe_id?: string;
    servings?: number;
    notes?: string;
}

// ─── Recipes ─────────────────────────────────────────────────────────────────

export interface RecipeStep {
    id: string;
    step_number: number;
    instruction: string;
    duration_min: number | null;
    is_active: boolean;
}

export interface RecipeIngredient {
    id: string;
    ingredient_id: string;
    ingredient_name: string;
    quantity: number;
    unit: string;
    prep_note: string | null;
    is_optional: boolean;
}

export interface Recipe {
    id: string;
    title: string;
    description: string;
    prep_time_min: number;
    cook_time_min: number;
    total_time_min: number;
    difficulty: "easy" | "medium" | "hard";
    servings: number;
    calories_per_serving: number | null;
    protein_g: number | null;
    carbs_g: number | null;
    fat_g: number | null;
    tags: string[];
    steps: RecipeStep[];
    recipe_ingredients: RecipeIngredient[];
}

export interface GenerateRecipeRequest {
    concept: string;
    dietary_restrictions?: string[];
    max_difficulty?: "easy" | "medium" | "hard";
    target_servings?: number;
}

// ─── Leftovers ───────────────────────────────────────────────────────────────

export type LeftoverStatus = "available" | "used" | "discarded";

export interface Leftover {
    id: string;
    meal_slot_id: string;
    recipe_id: string;
    remaining_servings: number;
    stored_date: string;
    expiry_date: string;
    status: LeftoverStatus;
    used_in_slot_id: string | null;
    recipe: { id: string; title: string } | null;
}

export interface CreateLeftoverRequest {
    meal_slot_id: string;
    recipe_id: string;
    remaining_servings: number;
    stored_date: string;
    expiry_date?: string;
}

// ─── Grocery ─────────────────────────────────────────────────────────────────

export type StoreSection = "produce" | "meat" | "dairy" | "bakery" | "pantry" | "frozen" | "other";
export type GroceryStatus = "draft" | "finalized" | "ordered";

export interface GroceryItem {
    id: string;
    grocery_list_id: string;
    ingredient_id: string;
    ingredient_name: string;
    quantity: number;
    unit: string;
    store_section: StoreSection;
    checked: boolean;
}

export interface GroceryList {
    id: string;
    meal_plan_id: string;
    generated_at: string;
    status: GroceryStatus;
    items: GroceryItem[];
}

// ─── Feedback ────────────────────────────────────────────────────────────────

export type FeedbackRating = "thumbs_up" | "thumbs_down";

export interface Feedback {
    id: string;
    meal_slot_id: string;
    recipe_id: string;
    rating: FeedbackRating;
    tags: string[] | null;
    note: string | null;
    created_at: string;
}

export interface CreateFeedbackRequest {
    meal_slot_id: string;
    recipe_id: string;
    rating: FeedbackRating;
    tags?: string[];
    note?: string;
}

// ─── Prep Plan ───────────────────────────────────────────────────────────────

export interface PrepTask {
    task_name: string;
    duration_min: number;
    is_active: boolean;
    batch_group: string | null;
    depends_on: string[];
}

export interface PrepPlan {
    tasks: PrepTask[];
    total_active_min: number;
    total_passive_min: number;
    recommended_sessions: string[];
    completed_tasks?: string[];
}

// ─── Pagination ──────────────────────────────────────────────────────────────

export interface PaginatedResponse<T> {
    items: T[];
    next_cursor: string | null;
}
