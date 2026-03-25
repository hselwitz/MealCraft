import {useState} from "react";
import {useNavigate, useParams} from "react-router-dom";
import {CheckCircle2, ChevronLeft, Circle, Clock, Flame, ThumbsDown, ThumbsUp, Users} from "lucide-react";
import {useRecipe} from "@/hooks/useApi";
import {Button} from "@/components/ui/button";
import {Badge} from "@/components/ui/badge";
import {Card, CardBody} from "@/components/ui/card";
import {apiPost} from "@/api/client";

const difficultyVariant = {
    easy: "green" as const,
    medium: "yellow" as const,
    hard: "red" as const,
};

export function RecipeDetail() {
    const {id} = useParams<{ id: string }>();
    const navigate = useNavigate();
    const {data: recipe, isLoading, error} = useRecipe(id);
    const [scaleFactor, setScaleFactor] = useState(1);
    const [completedSteps, setCompletedSteps] = useState<Set<number>>(new Set());
    const [feedbackSent, setFeedbackSent] = useState<"thumbs_up" | "thumbs_down" | null>(null);

    if (isLoading) {
        return (
            <div className="flex items-center justify-center min-h-64">
                <div className="animate-spin text-4xl">⏳</div>
            </div>
        );
    }

    if (error || !recipe) {
        return (
            <div className="text-center py-16">
                <p className="text-gray-500">Recipe not found.</p>
                <Button variant="ghost" onClick={() => navigate(-1)} className="mt-4">
                    Go back
                </Button>
            </div>
        );
    }

    const toggleStep = (stepNumber: number) => {
        const next = new Set(completedSteps);
        if (next.has(stepNumber)) next.delete(stepNumber);
        else next.add(stepNumber);
        setCompletedSteps(next);
    };

    const handleFeedback = async (rating: "thumbs_up" | "thumbs_down") => {
        try {
            await apiPost("/feedback", {recipe_id: recipe.id, rating});
            setFeedbackSent(rating);
        } catch {
            // ignore
        }
    };

    const scaledQty = (qty: number) => {
        const scaled = qty * scaleFactor;
        return scaled % 1 === 0 ? scaled.toString() : scaled.toFixed(2);
    };

    return (
        <div className="max-w-3xl mx-auto space-y-6">
            {/* Back button */}
            <button
                className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700"
                onClick={() => navigate(-1)}
            >
                <ChevronLeft size={16}/>
                Back
            </button>

            {/* Header */}
            <div>
                <div className="flex items-start justify-between gap-4">
                    <h1 className="text-3xl font-bold text-gray-900">{recipe.title}</h1>
                    <div className="flex gap-1 shrink-0">
                        {feedbackSent ? (
                            <Badge variant={feedbackSent === "thumbs_up" ? "green" : "red"}>
                                {feedbackSent === "thumbs_up" ? "👍 Rated" : "👎 Rated"}
                            </Badge>
                        ) : (
                            <>
                                <button
                                    className="p-2 rounded-lg hover:bg-green-50 text-gray-400 hover:text-green-600 transition-colors"
                                    onClick={() => handleFeedback("thumbs_up")}
                                    title="Thumbs up"
                                >
                                    <ThumbsUp size={20}/>
                                </button>
                                <button
                                    className="p-2 rounded-lg hover:bg-red-50 text-gray-400 hover:text-red-500 transition-colors"
                                    onClick={() => handleFeedback("thumbs_down")}
                                    title="Thumbs down"
                                >
                                    <ThumbsDown size={20}/>
                                </button>
                            </>
                        )}
                    </div>
                </div>
                <p className="text-gray-600 mt-2">{recipe.description}</p>

                <div className="flex flex-wrap items-center gap-3 mt-4">
                    <div className="flex items-center gap-1 text-sm text-gray-600">
                        <Clock size={15} className="text-gray-400"/>
                        <span>Prep: {recipe.prep_time_min}min</span>
                    </div>
                    <div className="flex items-center gap-1 text-sm text-gray-600">
                        <Clock size={15} className="text-gray-400"/>
                        <span>Cook: {recipe.cook_time_min}min</span>
                    </div>
                    {recipe.total_time_min && (
                        <div className="flex items-center gap-1 text-sm font-medium text-gray-700">
                            <Clock size={15} className="text-primary-500"/>
                            <span>Total: {recipe.total_time_min}min</span>
                        </div>
                    )}
                    <div className="flex items-center gap-1 text-sm text-gray-600">
                        <Users size={15} className="text-gray-400"/>
                        <span>{(recipe.servings * scaleFactor).toFixed(1)} servings</span>
                    </div>
                    {recipe.calories_per_serving && (
                        <div className="flex items-center gap-1 text-sm text-gray-600">
                            <Flame size={15} className="text-gray-400"/>
                            <span>{recipe.calories_per_serving} cal/serving</span>
                        </div>
                    )}
                    <Badge variant={difficultyVariant[recipe.difficulty] ?? "gray"}>
                        {recipe.difficulty}
                    </Badge>
                </div>

                <div className="flex flex-wrap gap-1 mt-3">
                    {recipe.tags?.map((tag) => (
                        <Badge key={tag} variant="blue">{tag}</Badge>
                    ))}
                </div>
            </div>

            {/* Nutrition */}
            {(recipe.protein_g || recipe.carbs_g || recipe.fat_g) && (
                <Card>
                    <CardBody className="flex gap-6">
                        {recipe.calories_per_serving && (
                            <div className="text-center">
                                <div className="text-2xl font-bold text-gray-900">{recipe.calories_per_serving}</div>
                                <div className="text-xs text-gray-500">Calories</div>
                            </div>
                        )}
                        {recipe.protein_g && (
                            <div className="text-center">
                                <div className="text-2xl font-bold text-blue-600">{recipe.protein_g}g</div>
                                <div className="text-xs text-gray-500">Protein</div>
                            </div>
                        )}
                        {recipe.carbs_g && (
                            <div className="text-center">
                                <div className="text-2xl font-bold text-yellow-600">{recipe.carbs_g}g</div>
                                <div className="text-xs text-gray-500">Carbs</div>
                            </div>
                        )}
                        {recipe.fat_g && (
                            <div className="text-center">
                                <div className="text-2xl font-bold text-orange-600">{recipe.fat_g}g</div>
                                <div className="text-xs text-gray-500">Fat</div>
                            </div>
                        )}
                    </CardBody>
                </Card>
            )}

            {/* Scale servings */}
            <div className="flex items-center gap-3">
                <span className="text-sm font-medium text-gray-700">Scale servings:</span>
                {[0.5, 1, 1.5, 2, 3].map((factor) => (
                    <button
                        key={factor}
                        className={[
                            "px-2.5 py-1 rounded-lg text-sm font-medium transition-colors",
                            scaleFactor === factor
                                ? "bg-primary-600 text-white"
                                : "bg-gray-100 text-gray-600 hover:bg-gray-200",
                        ].join(" ")}
                        onClick={() => setScaleFactor(factor)}
                    >
                        {factor}x
                    </button>
                ))}
            </div>

            {/* Ingredients */}
            <div>
                <h2 className="text-xl font-semibold text-gray-900 mb-3">Ingredients</h2>
                <ul className="space-y-1.5">
                    {recipe.recipe_ingredients?.map((ri) => (
                        <li key={ri.id} className="flex items-start gap-2 text-sm">
                            <span className="text-gray-300 mt-0.5">•</span>
                            <span>
                <span className="font-medium text-gray-800">
                  {scaledQty(ri.quantity)} {ri.unit}
                </span>{" "}
                                <span className="text-gray-700">{ri.ingredient_name}</span>
                                {ri.prep_note && (
                                    <span className="text-gray-400">, {ri.prep_note}</span>
                                )}
                                {ri.is_optional && (
                                    <span className="ml-1 text-xs text-gray-400">(optional)</span>
                                )}
              </span>
                        </li>
                    ))}
                </ul>
            </div>

            {/* Steps */}
            <div>
                {(() => {
                    const steps = recipe.steps ?? [];
                    const totalTime = steps.reduce((sum, s) => sum + (s.duration_min ?? 1), 0);
                    const doneTime = steps
                        .filter((s) => completedSteps.has(s.step_number))
                        .reduce((sum, s) => sum + (s.duration_min ?? 1), 0);
                    const pct = totalTime > 0 ? (doneTime / totalTime) * 100 : 0;

                    return (
                        <>
                            <div className="flex items-center justify-between mb-2">
                                <h2 className="text-xl font-semibold text-gray-900">Instructions</h2>
                                {steps.length > 0 && (
                                    <span className="text-sm text-gray-500">
                                        {completedSteps.size}/{steps.length} steps done
                                    </span>
                                )}
                            </div>
                            {steps.length > 0 && completedSteps.size > 0 && (
                                <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden mb-3">
                                    <div
                                        className="h-full bg-green-500 rounded-full transition-all"
                                        style={{width: `${pct}%`}}
                                    />
                                </div>
                            )}
                        </>
                    );
                })()}
                <div className="space-y-3">
                    {recipe.steps?.map((step) => (
                        <div
                            key={step.id}
                            className={[
                                "flex gap-3 p-3 rounded-lg border cursor-pointer transition-colors",
                                completedSteps.has(step.step_number)
                                    ? "bg-green-50 border-green-200"
                                    : "bg-white border-gray-200 hover:bg-gray-50",
                            ].join(" ")}
                            onClick={() => toggleStep(step.step_number)}
                        >
                            <div className="shrink-0 mt-0.5">
                                {completedSteps.has(step.step_number) ? (
                                    <CheckCircle2 size={20} className="text-green-500"/>
                                ) : (
                                    <Circle size={20} className="text-gray-300"/>
                                )}
                            </div>
                            <div className="flex-1">
                                <div className="flex items-center gap-2 mb-1">
                  <span className="text-sm font-semibold text-gray-500">
                    Step {step.step_number}
                  </span>
                                    {step.duration_min && (
                                        <span className="text-xs text-gray-400">{step.duration_min}min</span>
                                    )}
                                    <Badge variant={step.is_active ? "blue" : "gray"} className="text-[10px]">
                                        {step.is_active ? "active" : "passive"}
                                    </Badge>
                                </div>
                                <p
                                    className={[
                                        "text-sm leading-relaxed",
                                        completedSteps.has(step.step_number) ? "text-gray-400 line-through" : "text-gray-700",
                                    ].join(" ")}
                                >
                                    {step.instruction}
                                </p>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}
