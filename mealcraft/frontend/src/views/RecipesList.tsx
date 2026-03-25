import {useState} from "react";
import {BookOpen, Wand2} from "lucide-react";
import {useGenerateRecipe, useRecipes} from "@/hooks/useApi";
import type {RecipeSummary} from "@/types";
import {Button} from "@/components/ui/button";
import {Input} from "@/components/ui/input";
import {RecipeCard} from "@/components/RecipeCard";
import {RecipeCardSkeleton} from "@/components/ui/skeleton";

export function RecipesList() {
    const {data: recipes, isLoading} = useRecipes();
    const generateRecipe = useGenerateRecipe();
    const [showGenerateForm, setShowGenerateForm] = useState(false);
    const [concept, setConcept] = useState("");
    const [restrictions, setRestrictions] = useState("");

    const handleGenerate = async () => {
        if (!concept.trim()) return;
        await generateRecipe.mutateAsync({
            concept: concept.trim(),
            dietary_restrictions: restrictions
                ? restrictions.split(",").map((s) => s.trim()).filter(Boolean)
                : [],
            max_difficulty: "medium",
            target_servings: 4,
        });
        setConcept("");
        setRestrictions("");
        setShowGenerateForm(false);
    };

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">Recipes</h1>
                    <p className="text-sm text-gray-500 mt-1">
                        {recipes?.length ?? 0} recipe{recipes?.length !== 1 ? "s" : ""} saved
                    </p>
                </div>

                <Button
                    onClick={() => setShowGenerateForm(!showGenerateForm)}
                    className="flex items-center gap-2"
                >
                    <Wand2 size={16}/>
                    Generate Recipe
                </Button>
            </div>

            {/* Generate form */}
            {showGenerateForm && (
                <div className="bg-white rounded-xl border border-gray-200 p-4 space-y-3 shadow-sm">
                    <h3 className="font-semibold text-gray-800">Generate New Recipe</h3>
                    <Input
                        label="Meal concept"
                        placeholder="e.g. Spicy Thai peanut noodles with tofu"
                        value={concept}
                        onChange={(e) => setConcept(e.target.value)}
                        onKeyDown={(e) => e.key === "Enter" && handleGenerate()}
                    />
                    <Input
                        label="Dietary restrictions (optional)"
                        placeholder="e.g. vegetarian, gluten-free"
                        value={restrictions}
                        onChange={(e) => setRestrictions(e.target.value)}
                        hint="Comma-separated list"
                    />
                    <div className="flex gap-2">
                        <Button onClick={handleGenerate} loading={generateRecipe.isPending} disabled={!concept.trim()}>
                            Generate
                        </Button>
                        <Button variant="ghost" onClick={() => setShowGenerateForm(false)}>
                            Cancel
                        </Button>
                    </div>
                </div>
            )}

            {!isLoading && recipes?.length === 0 && (
                <div className="text-center py-16 text-gray-400">
                    <BookOpen size={48} className="mx-auto mb-3 opacity-30"/>
                    <p>No recipes yet.</p>
                    <p className="text-sm mt-1">Generate a meal plan or create individual recipes.</p>
                </div>
            )}

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {isLoading
                    ? Array.from({length: 6}).map((_, i) => <RecipeCardSkeleton key={i}/>)
                    : recipes?.map((recipe) => (
                        <RecipeCard key={recipe.id} recipe={recipe as unknown as RecipeSummary}/>
                    ))
                }
            </div>
        </div>
    );
}
