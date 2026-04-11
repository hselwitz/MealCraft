import {useEffect, useState} from "react";
import {closestCenter, DndContext, DragEndEvent} from "@dnd-kit/core";
import {ChevronLeft, ChevronRight, Wand2} from "lucide-react";
import {
    useCreatePlan,
    useCreateSlot,
    useDeleteSlot,
    usePlan,
    usePlans,
    useRegenerateSlot,
    useUpdateSlot,
} from "@/hooks/useApi";
import {apiPostStream} from "@/api/client";
import {useSettings} from "@/hooks/useSettings";
import type {MealType} from "@/types";
import {Button} from "@/components/ui/button";
import {MealSlotCard} from "@/components/MealSlot";
import {useQueryClient} from "@tanstack/react-query";

const MEAL_TYPES: MealType[] = ["breakfast", "lunch", "dinner", "snack"];
const TODAY = new Date().toISOString().split("T")[0];

function addDays(base: Date, n: number): string {
    const d = new Date(base);
    d.setDate(d.getDate() + n);
    return d.toISOString().split("T")[0];
}

function getVisibleDates(dayOffset: number): string[] {
    const base = new Date();
    return Array.from({length: 7}, (_, i) => addDays(base, dayOffset + i));
}

function fmtDate(iso: string) {
    return new Date(iso + "T12:00:00").toLocaleDateString("en-US", {month: "short", day: "numeric"});
}

function fmtDayLabel(iso: string) {
    return new Date(iso + "T12:00:00").toLocaleDateString("en-US", {weekday: "short"});
}

export function WeeklyPlanner() {
    const qc = useQueryClient();
    const [dayOffset, setDayOffset] = useState(0);
    const [selectedDayIndex, setSelectedDayIndex] = useState(0);
    const [error, setError] = useState<string | null>(null);
    const [generating, setGenerating] = useState(false);
    const [genStatus, setGenStatus] = useState<string>("");

    const visibleDates = getVisibleDates(dayOffset);

    const [settings] = useSettings();
    const {data: plans} = usePlans();
    const createPlan = useCreatePlan();
    const createSlot = useCreateSlot();
    const deleteSlot = useDeleteSlot();
    const updateSlot = useUpdateSlot();
    const regenerateSlot = useRegenerateSlot();

    // Auto-create the one persistent plan if none exists
    const activePlan = plans?.find((p) => p.status === "active" || p.status === "draft");
    useEffect(() => {
        if (plans !== undefined && !activePlan && !createPlan.isPending) {
            const far = addDays(new Date(), 3650);
            createPlan.mutate({
                name: "My Meal Plan",
                start_date: TODAY,
                end_date: far,
                slots_config: [],
            });
        }
    }, [plans]);

    const {data: plan, isLoading: planLoading} = usePlan(activePlan?.id);

    const getSlot = (date: string, mealType: MealType) =>
        plan?.slots.find((s) => s.date === date && s.meal_type === mealType);

    const unfilledCount = plan?.slots.filter((s) => s.status === "planned" && !s.recipe_id).length ?? 0;

    const handleAddSlot = async (date: string, mealType: MealType) => {
        if (!activePlan) return;
        await createSlot.mutateAsync({planId: activePlan.id, date, mealType});
    };

    const handleRemoveSlot = async (slotId: string) => {
        if (!activePlan) return;
        await deleteSlot.mutateAsync({planId: activePlan.id, slotId});
    };

    const handleRegenerate = async (slotId: string) => {
        if (!activePlan) return;
        await regenerateSlot.mutateAsync({planId: activePlan.id, slotId});
    };

    const handleGenerate = async () => {
        if (!activePlan) return;
        setError(null);
        setGenerating(true);
        setGenStatus("Starting...");
        try {
            await new Promise<void>((resolve, reject) => {
                apiPostStream(
                    `/plans/${activePlan.id}/generate`,
                    {
                        preferences: {
                            max_difficulty: settings.maxDifficulty,
                            ingredient_overlap: settings.ingredientOverlap,
                            calorie_target: settings.calorieTarget,
                            household_size: settings.defaultServings,
                            dietary_restrictions: settings.dietaryRestrictions,
                            cuisine_preferences: settings.cuisinePreferences,
                            meal_prep_focus: settings.mealPrepFocus,
                        },
                    },
                    (raw) => {
                        try {
                            const event = JSON.parse(raw);
                            if (event.error) reject(new Error(event.error));
                            else if (event.message) setGenStatus(event.message);
                        } catch { /* ignore */
                        }
                    },
                    resolve,
                    reject,
                );
            });
            setGenStatus("Loading your plan...");
            await qc.invalidateQueries({queryKey: ["plans", activePlan.id]});
        } catch (e: unknown) {
            setError(e instanceof Error ? e.message : "Failed to generate");
        } finally {
            setGenerating(false);
            setGenStatus("");
        }
    };

    const handleDragEnd = async (event: DragEndEvent) => {
        const {active, over} = event;
        if (!over || !plan || !activePlan) return;
        const draggedSlotId = active.id as string;
        const targetSlotId = (over.id as string).replace("drop-", "");
        if (draggedSlotId === targetSlotId) return;
        const draggedSlot = plan.slots.find((s) => s.id === draggedSlotId);
        const targetSlot = plan.slots.find((s) => s.id === targetSlotId);
        if (!draggedSlot || !targetSlot) return;
        await updateSlot.mutateAsync({
            planId: activePlan.id,
            slotId: draggedSlotId,
            body: {recipe_id: targetSlot.recipe_id ?? undefined}
        });
        await updateSlot.mutateAsync({
            planId: activePlan.id,
            slotId: targetSlotId,
            body: {recipe_id: draggedSlot.recipe_id ?? undefined}
        });
    };

    const navigate = (delta: number) => {
        setDayOffset((o) => o + delta);
        setSelectedDayIndex(0);
    };

    return (
        <div className="space-y-4">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">Planner</h1>
                </div>

                <div className="flex items-center gap-2">
                    {/* Day navigation */}
                    <div className="flex items-center gap-1">
                        <button className="p-1.5 rounded hover:bg-gray-100 text-gray-500" onClick={() => navigate(-1)}>
                            <ChevronLeft size={18}/>
                        </button>
                        <button
                            className="text-xs px-2 py-1 rounded hover:bg-gray-100 text-gray-500 min-w-[110px] text-center"
                            onClick={() => {
                                setDayOffset(0);
                                setSelectedDayIndex(0);
                            }}
                        >
                            {fmtDate(visibleDates[0])} – {fmtDate(visibleDates[6])}
                        </button>
                        <button className="p-1.5 rounded hover:bg-gray-100 text-gray-500" onClick={() => navigate(1)}>
                            <ChevronRight size={18}/>
                        </button>
                    </div>

                    <Button
                        size="sm"
                        onClick={handleGenerate}
                        loading={generating}
                        disabled={unfilledCount === 0}
                        className="flex items-center gap-1"
                    >
                        <Wand2 size={14}/>
                        Generate{unfilledCount > 0 ? ` (${unfilledCount})` : ""}
                    </Button>
                </div>
            </div>

            {error && (
                <div
                    className="rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700 flex items-center justify-between">
                    <span>{error}</span>
                    <button className="ml-4 text-red-400 hover:text-red-600" onClick={() => setError(null)}>✕</button>
                </div>
            )}

            {/* Desktop grid */}
            <DndContext collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
                <div className="hidden sm:block overflow-x-auto">
                    <table className="w-full border-collapse">
                        <thead>
                        <tr>
                            <th className="w-20 p-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wide">Meal</th>
                            {visibleDates.map((date) => {
                                const isToday = date === TODAY;
                                return (
                                    <th key={date} className="p-2 text-center min-w-[130px]">
                                        <div
                                            className={`text-xs font-medium uppercase ${isToday ? "text-primary-600" : "text-gray-500"}`}>
                                            {fmtDayLabel(date)}
                                        </div>
                                        <div
                                            className={`text-sm font-semibold ${isToday ? "text-primary-700" : "text-gray-800"}`}>
                                            {fmtDate(date)}
                                        </div>
                                        {isToday && (
                                            <div className="flex justify-center mt-0.5">
                                                <span className="w-1.5 h-1.5 rounded-full bg-primary-500 inline-block"/>
                                            </div>
                                        )}
                                    </th>
                                );
                            })}
                        </tr>
                        </thead>
                        <tbody>
                        {MEAL_TYPES.map((mealType) => (
                            <tr key={mealType} className="border-t border-gray-100">
                                <td className="p-2 text-xs font-medium text-gray-500 capitalize align-top pt-3">{mealType}</td>
                                {visibleDates.map((date) => {
                                    const slot = getSlot(date, mealType);
                                    return (
                                        <td key={date} className="p-1.5 align-top group">
                                            {slot ? (
                                                <MealSlotCard
                                                    slot={slot}
                                                    planId={activePlan!.id}
                                                    onRegenerate={handleRegenerate}
                                                    onRemove={handleRemoveSlot}
                                                    isLoading={regenerateSlot.isPending && regenerateSlot.variables?.slotId === slot.id}
                                                />
                                            ) : (
                                                <div
                                                    onClick={() => handleAddSlot(date, mealType)}
                                                    className="min-h-[80px] rounded-lg border border-dashed border-gray-200 bg-gray-50 flex items-center justify-center cursor-pointer hover:border-primary-300 hover:bg-primary-50 transition-colors group/add"
                                                >
                                                    <span
                                                        className="text-xl font-light text-gray-300 group-hover/add:text-primary-400 transition-colors">+</span>
                                                </div>
                                            )}
                                        </td>
                                    );
                                })}
                            </tr>
                        ))}
                        </tbody>
                    </table>
                </div>
            </DndContext>

            {/* Mobile day-by-day view */}
            <div className="sm:hidden space-y-3">
                <div className="flex gap-1 overflow-x-auto pb-1 -mx-4 px-4">
                    {visibleDates.map((date, i) => {
                        const hasRecipe = MEAL_TYPES.some((mt) => getSlot(date, mt)?.recipe);
                        const isToday = date === TODAY;
                        const isSelected = selectedDayIndex === i;
                        return (
                            <button
                                key={date}
                                onClick={() => setSelectedDayIndex(i)}
                                className={[
                                    "flex-shrink-0 flex flex-col items-center px-3 py-2 rounded-xl text-xs font-medium transition-colors",
                                    isSelected
                                        ? "bg-primary-600 text-white"
                                        : isToday
                                            ? "bg-primary-50 text-primary-700 ring-1 ring-primary-300"
                                            : "bg-gray-100 text-gray-600",
                                ].join(" ")}
                            >
                                <span>{fmtDayLabel(date)}</span>
                                <span className="font-semibold">
                                    {new Date(date + "T12:00:00").toLocaleDateString("en-US", {day: "numeric"})}
                                </span>
                                {(hasRecipe || isToday) && (
                                    <span className={[
                                        "w-1.5 h-1.5 rounded-full mt-1",
                                        isSelected ? "bg-white/60" : isToday ? "bg-primary-400" : "bg-primary-300",
                                    ].join(" ")}/>
                                )}
                            </button>
                        );
                    })}
                </div>

                <div className="space-y-2">
                    {MEAL_TYPES.map((mealType) => {
                        const slot = getSlot(visibleDates[selectedDayIndex], mealType);
                        return (
                            <div key={mealType}>
                                <div
                                    className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-1 px-1">{mealType}</div>
                                {slot ? (
                                    <MealSlotCard
                                        slot={slot}
                                        planId={activePlan!.id}
                                        onRegenerate={handleRegenerate}
                                        onRemove={handleRemoveSlot}
                                        isLoading={regenerateSlot.isPending && regenerateSlot.variables?.slotId === slot.id}
                                    />
                                ) : (
                                    <div
                                        onClick={() => handleAddSlot(visibleDates[selectedDayIndex], mealType)}
                                        className="h-14 rounded-xl border border-dashed border-gray-200 bg-gray-50 flex items-center justify-center cursor-pointer hover:border-primary-300 hover:bg-primary-50 transition-colors group/add"
                                    >
                                        <span
                                            className="text-xl font-light text-gray-300 group-hover/add:text-primary-400 transition-colors">+</span>
                                    </div>
                                )}
                            </div>
                        );
                    })}
                </div>
            </div>

            {planLoading && (
                <div className="hidden sm:grid grid-cols-8 gap-1.5 animate-pulse">
                    <div/>
                    {Array.from({length: 7}).map((_, i) => (
                        <div key={i} className="space-y-1.5">
                            {Array.from({length: 4}).map((_, j) => (
                                <div key={j} className="h-20 rounded-lg bg-gray-100"/>
                            ))}
                        </div>
                    ))}
                </div>
            )}

            {generating && (
                <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50">
                    <div className="bg-white rounded-xl p-6 shadow-xl text-center max-w-sm w-full mx-4">
                        <div className="flex justify-center mb-4">
                            <svg className="animate-spin h-8 w-8 text-primary-600" fill="none" viewBox="0 0 24 24">
                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor"
                                        strokeWidth="4"/>
                                <path className="opacity-75" fill="currentColor"
                                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                            </svg>
                        </div>
                        <p className="text-gray-800 font-semibold mb-1">Generating your meal plan</p>
                        <p className="text-gray-500 text-sm min-h-[20px]">{genStatus}</p>
                    </div>
                </div>
            )}
        </div>
    );
}
