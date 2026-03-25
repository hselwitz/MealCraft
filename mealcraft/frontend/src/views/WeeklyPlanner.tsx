import {useState} from "react";
import {closestCenter, DndContext, DragEndEvent} from "@dnd-kit/core";
import {ChevronLeft, ChevronRight, Plus, Wand2} from "lucide-react";
import {useCreatePlan, usePlan, usePlans, useRegenerateSlot, useUpdateSlot} from "@/hooks/useApi";
import {apiPostStream} from "@/api/client";
import {useSettings} from "@/hooks/useSettings";
import type {MealType, SlotStatus} from "@/types";
import {Button} from "@/components/ui/button";
import {MealSlotCard} from "@/components/MealSlot";
import {Badge} from "@/components/ui/badge";
import {useQueryClient} from "@tanstack/react-query";

const MEAL_TYPES: MealType[] = ["breakfast", "lunch", "dinner", "snack"];
const DAY_LABELS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

function getWeekDates(startDate: Date): string[] {
    const dates: string[] = [];
    const d = new Date(startDate);
    const day = d.getDay();
    const diff = d.getDate() - day + (day === 0 ? -6 : 1);
    d.setDate(diff);
    for (let i = 0; i < 7; i++) {
        const curr = new Date(d);
        curr.setDate(d.getDate() + i);
        dates.push(curr.toISOString().split("T")[0]);
    }
    return dates;
}

function getMonday(date: Date): Date {
    const d = new Date(date);
    const day = d.getDay();
    const diff = d.getDate() - day + (day === 0 ? -6 : 1);
    d.setDate(diff);
    return d;
}

export function WeeklyPlanner() {
    const qc = useQueryClient();
    const [weekOffset, setWeekOffset] = useState(0);
    const [selectedPlanId, setSelectedPlanId] = useState<string | null>(null);
    const [selectedDayIndex, setSelectedDayIndex] = useState(new Date().getDay() === 0 ? 6 : new Date().getDay() - 1);
    const [error, setError] = useState<string | null>(null);
    const [generating, setGenerating] = useState(false);
    const [genStatus, setGenStatus] = useState<string>("");

    const baseDate = getMonday(new Date());
    baseDate.setDate(baseDate.getDate() + weekOffset * 7);
    const weekDates = getWeekDates(baseDate);

    const [settings] = useSettings();
    const {data: plans} = usePlans();
    const createPlan = useCreatePlan();
    const updateSlot = useUpdateSlot();
    const regenerateSlot = useRegenerateSlot();

    // Resolve active plan ID — prefer explicitly selected, then first draft/active
    const activePlanId = selectedPlanId ?? plans?.find(
        (p) => p.status === "active" || p.status === "draft"
    )?.id ?? null;

    // Full plan with slots from React Query (persists across navigation)
    const {data: plan, isLoading: planLoading} = usePlan(activePlanId ?? undefined);

    const handleCreateWeek = async () => {
        setError(null);
        try {
            const slots_config = weekDates.flatMap((date) =>
                MEAL_TYPES.map((meal_type) => ({date, meal_type}))
            );
            const created = await createPlan.mutateAsync({
                name: `Week of ${weekDates[0]}`,
                start_date: weekDates[0],
                end_date: weekDates[6],
                calorie_target: settings.calorieTarget,
                slots_config,
            });
            setSelectedPlanId(created.id);
        } catch (e: unknown) {
            setError(e instanceof Error ? e.message : "Failed to create week");
        }
    };

    const handleGeneratePlan = async () => {
        if (!activePlanId) return;
        setError(null);
        setGenerating(true);
        setGenStatus("Starting...");
        try {
            await new Promise<void>((resolve, reject) => {
                apiPostStream(
                    `/plans/${activePlanId}/generate`,
                    {
                        preferences: {
                            max_difficulty: settings.maxDifficulty,
                            ingredient_overlap: settings.ingredientOverlap,
                            calorie_target: settings.calorieTarget,
                            household_size: settings.defaultServings,
                            dietary_restrictions: settings.dietaryRestrictions,
                            cuisine_preferences: settings.cuisinePreferences,
                        }
                    },
                    (raw) => {
                        try {
                            const event = JSON.parse(raw);
                            if (event.error) reject(new Error(event.error));
                            else if (event.message) setGenStatus(event.message);
                        } catch { /* ignore parse errors */
                        }
                    },
                    resolve,
                    reject,
                );
            });
            setGenStatus("Loading your plan...");
            // Refresh the plan in React Query cache
            await qc.invalidateQueries({queryKey: ["plans", activePlanId]});
        } catch (e: unknown) {
            setError(e instanceof Error ? e.message : "Failed to generate plan");
        } finally {
            setGenerating(false);
            setGenStatus("");
        }
    };

    const handleStatusChange = async (slotId: string, status: string) => {
        if (!activePlanId) return;
        await updateSlot.mutateAsync({
            planId: activePlanId,
            slotId,
            body: {status: status as SlotStatus},
        });
    };

    const handleRegenerate = async (slotId: string) => {
        if (!activePlanId) return;
        await regenerateSlot.mutateAsync({planId: activePlanId, slotId});
    };

    const handleDragEnd = async (event: DragEndEvent) => {
        const {active, over} = event;
        if (!over || !plan || !activePlanId) return;

        const draggedSlotId = active.id as string;
        const targetSlotId = (over.id as string).replace("drop-", "");
        if (draggedSlotId === targetSlotId) return;

        const draggedSlot = plan.slots.find((s) => s.id === draggedSlotId);
        const targetSlot = plan.slots.find((s) => s.id === targetSlotId);
        if (!draggedSlot || !targetSlot) return;

        await updateSlot.mutateAsync({
            planId: activePlanId,
            slotId: draggedSlotId,
            body: {recipe_id: targetSlot.recipe_id ?? undefined},
        });
        await updateSlot.mutateAsync({
            planId: activePlanId,
            slotId: targetSlotId,
            body: {recipe_id: draggedSlot.recipe_id ?? undefined},
        });
    };

    const getSlot = (date: string, mealType: MealType) =>
        plan?.slots.find((s) => s.date === date && s.meal_type === mealType);

    const hasRecipes = plan?.slots.some((s) => s.recipe != null);

    return (
        <div className="space-y-4">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">Weekly Planner</h1>
                    {plan && (
                        <p className="text-sm text-gray-500">
                            {plan.name} •{" "}
                            <Badge
                                variant={plan.status === "active" ? "green" : plan.status === "draft" ? "yellow" : "gray"}>
                                {plan.status}
                            </Badge>
                        </p>
                    )}
                </div>

                <div className="flex items-center gap-2">
                    <div className="flex items-center gap-1">
                        <button className="p-1.5 rounded hover:bg-gray-100 text-gray-500"
                                onClick={() => setWeekOffset((o) => o - 1)}>
                            <ChevronLeft size={18}/>
                        </button>
                        <span className="text-sm text-gray-600 min-w-[120px] text-center">
                            {weekDates[0]} – {weekDates[6]}
                        </span>
                        <button className="p-1.5 rounded hover:bg-gray-100 text-gray-500"
                                onClick={() => setWeekOffset((o) => o + 1)}>
                            <ChevronRight size={18}/>
                        </button>
                    </div>

                    {!plan ? (
                        <Button variant="outline" size="sm" onClick={handleCreateWeek} loading={createPlan.isPending}
                                className="flex items-center gap-1">
                            <Plus size={14}/>
                            Create Week
                        </Button>
                    ) : (
                        <Button size="sm" onClick={handleGeneratePlan} loading={generating}
                                className="flex items-center gap-1">
                            <Wand2 size={14}/>
                            {hasRecipes ? "Regenerate Plan" : "Generate Plan"}
                        </Button>
                    )}
                </div>
            </div>

            {error && (
                <div
                    className="rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700 flex items-center justify-between">
                    <span>{error}</span>
                    <button className="ml-4 text-red-400 hover:text-red-600" onClick={() => setError(null)}>✕</button>
                </div>
            )}

            {/* ── Desktop grid ── */}
            <DndContext collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
                <div className="hidden sm:block overflow-x-auto">
                    <table className="w-full border-collapse">
                        <thead>
                        <tr>
                            <th className="w-20 p-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wide">Meal</th>
                            {weekDates.map((date, i) => (
                                <th key={date} className="p-2 text-center min-w-[130px]">
                                    <div className="text-xs font-medium text-gray-500 uppercase">{DAY_LABELS[i]}</div>
                                    <div className="text-sm font-semibold text-gray-800">
                                        {new Date(date + "T12:00:00").toLocaleDateString("en-US", {
                                            month: "short",
                                            day: "numeric"
                                        })}
                                    </div>
                                </th>
                            ))}
                        </tr>
                        </thead>
                        <tbody>
                        {MEAL_TYPES.map((mealType) => (
                            <tr key={mealType} className="border-t border-gray-100">
                                <td className="p-2 text-xs font-medium text-gray-500 capitalize align-top pt-3">{mealType}</td>
                                {weekDates.map((date) => {
                                    const slot = getSlot(date, mealType);
                                    return (
                                        <td key={date} className="p-1.5 align-top group">
                                            {slot ? (
                                                <MealSlotCard
                                                    slot={slot}
                                                    planId={activePlanId!}
                                                    onStatusChange={handleStatusChange}
                                                    onRegenerate={handleRegenerate}
                                                    isLoading={regenerateSlot.isPending && regenerateSlot.variables?.slotId === slot.id}
                                                />
                                            ) : (
                                                <div
                                                    className="min-h-[60px] rounded-lg border border-dashed border-gray-200 bg-gray-50"/>
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

            {/* ── Mobile day-by-day view ── */}
            <div className="sm:hidden space-y-3">
                {/* Day selector */}
                <div className="flex gap-1 overflow-x-auto pb-1 -mx-4 px-4">
                    {weekDates.map((date, i) => {
                        const hasRecipe = MEAL_TYPES.some((mt) => getSlot(date, mt)?.recipe);
                        return (
                            <button
                                key={date}
                                onClick={() => setSelectedDayIndex(i)}
                                className={[
                                    "flex-shrink-0 flex flex-col items-center px-3 py-2 rounded-xl text-xs font-medium transition-colors",
                                    selectedDayIndex === i
                                        ? "bg-primary-600 text-white"
                                        : "bg-gray-100 text-gray-600",
                                ].join(" ")}
                            >
                                <span>{DAY_LABELS[i]}</span>
                                <span className="font-semibold">
                                    {new Date(date + "T12:00:00").toLocaleDateString("en-US", {day: "numeric"})}
                                </span>
                                {hasRecipe && (
                                    <span
                                        className={`w-1.5 h-1.5 rounded-full mt-1 ${selectedDayIndex === i ? "bg-white/60" : "bg-primary-400"}`}/>
                                )}
                            </button>
                        );
                    })}
                </div>

                {/* Meals for selected day */}
                <div className="space-y-2">
                    {MEAL_TYPES.map((mealType) => {
                        const slot = getSlot(weekDates[selectedDayIndex], mealType);
                        return (
                            <div key={mealType}>
                                <div
                                    className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-1 px-1">{mealType}</div>
                                {slot ? (
                                    <MealSlotCard
                                        slot={slot}
                                        planId={activePlanId!}
                                        onStatusChange={handleStatusChange}
                                        onRegenerate={handleRegenerate}
                                        isLoading={regenerateSlot.isPending && regenerateSlot.variables?.slotId === slot.id}
                                    />
                                ) : (
                                    <div className="h-14 rounded-xl border border-dashed border-gray-200 bg-gray-50"/>
                                )}
                            </div>
                        );
                    })}
                </div>
            </div>

            {planLoading && !plan && (
                <div className="text-center py-8 text-gray-400 text-sm">Loading plan...</div>
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
