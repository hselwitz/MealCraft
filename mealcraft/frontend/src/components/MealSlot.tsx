import {useNavigate} from "react-router-dom";
import {GripVertical, RefreshCw, Utensils} from "lucide-react";
import {useDraggable, useDroppable} from "@dnd-kit/core";
import type {MealSlot as MealSlotType} from "@/types";
import {Badge} from "./ui/badge";

interface MealSlotProps {
    slot: MealSlotType;
    planId: string;
    onStatusChange: (slotId: string, status: string) => void;
    onRegenerate: (slotId: string) => void;
    isLoading?: boolean;
}

const statusColors: Record<string, string> = {
    planned: "bg-white",
    cooked: "bg-green-50",
    skipped: "bg-gray-50 border-dashed border-gray-200 opacity-50 hover:opacity-100",
    eating_out: "bg-orange-50",
};

export function MealSlotCard({
                                 slot,
                                 planId,
                                 onStatusChange,
                                 onRegenerate,
                                 isLoading,
                             }: MealSlotProps) {
    const navigate = useNavigate();

    const {
        attributes,
        listeners,
        setNodeRef: setDraggableRef,
        isDragging,
    } = useDraggable({id: slot.id, data: {slot}});

    const {setNodeRef: setDroppableRef, isOver} = useDroppable({
        id: `drop-${slot.id}`,
        data: {slot},
    });

    return (
        <div
            ref={(el) => {
                setDraggableRef(el);
                setDroppableRef(el);
            }}
            className={[
                "relative rounded-lg border transition-all min-h-[80px] p-2 text-xs",
                statusColors[slot.status] ?? "bg-white",
                isDragging ? "opacity-50 shadow-lg scale-95" : "",
                isOver ? "ring-2 ring-primary-400 border-primary-300" : "border-gray-200",
                isLoading ? "animate-pulse" : "",
            ].join(" ")}
            {...attributes}
        >
            {slot.recipe ? (
                <div>
                    <div className="flex items-start gap-1">
                        <span
                            className="shrink-0 mt-0.5 cursor-grab active:cursor-grabbing text-gray-300 hover:text-gray-400"
                            {...listeners}
                        >
                            <GripVertical size={12}/>
                        </span>
                        <p
                            className="font-medium text-gray-800 leading-tight line-clamp-2 hover:text-primary-700 cursor-pointer"
                            onClick={() => navigate(`/recipes/${slot.recipe_id}`)}
                        >
                            {slot.recipe.title}
                        </p>
                    </div>
                    <div className="flex items-center gap-1 mt-1 text-gray-500">
                        <span>{slot.recipe.prep_time_min + slot.recipe.cook_time_min}min</span>
                        {slot.recipe.calories_per_serving && (
                            <span>• {slot.recipe.calories_per_serving} cal</span>
                        )}
                    </div>
                    <Badge
                        variant={
                            slot.recipe.difficulty === "easy"
                                ? "green"
                                : slot.recipe.difficulty === "medium"
                                    ? "yellow"
                                    : "red"
                        }
                        className="mt-1"
                    >
                        {slot.recipe.difficulty}
                    </Badge>
                </div>
            ) : slot.status === "eating_out" ? (
                <div className="flex items-center gap-1 text-orange-600" {...listeners}>
                    <Utensils size={12}/>
                    <span>Eating out</span>
                </div>
            ) : slot.status === "skipped" ? (
                <button
                    className="w-full h-full flex items-center justify-center text-gray-300 hover:text-primary-400 transition-colors"
                    onClick={() => onStatusChange(slot.id, "planned")}
                >
                    <span className="text-xl font-light leading-none">+</span>
                </button>
            ) : (
                <div className="text-gray-400 italic" {...listeners}>No meal planned</div>
            )}

            {/* Action buttons */}
            <div
                className="absolute top-1 right-1 flex gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity"
                onClick={(e) => e.stopPropagation()}
            >
                {slot.status === "planned" && (
                    <button
                        className="p-0.5 rounded hover:bg-gray-200 text-gray-500 hover:text-primary-600"
                        title="Regenerate recipe"
                        onClick={() => onRegenerate(slot.id)}
                    >
                        <RefreshCw size={11}/>
                    </button>
                )}
            </div>

            {/* Status toggle buttons — hidden for bare skipped slots */}
            {slot.status !== "skipped" && (
                <div
                    className="flex gap-1 mt-1.5"
                    onClick={(e) => e.stopPropagation()}
                >
                    {slot.status !== "eating_out" && (
                        <button
                            className="text-[10px] px-1.5 py-0.5 rounded bg-orange-100 text-orange-700 hover:bg-orange-200"
                            onClick={() => onStatusChange(slot.id, "eating_out")}
                        >
                            Out
                        </button>
                    )}
                    <button
                        className="text-[10px] px-1.5 py-0.5 rounded bg-gray-100 text-gray-600 hover:bg-gray-200"
                        onClick={() => onStatusChange(slot.id, "skipped")}
                    >
                        Remove
                    </button>
                    {slot.status === "eating_out" && (
                        <button
                            className="text-[10px] px-1.5 py-0.5 rounded bg-green-100 text-green-700 hover:bg-green-200"
                            onClick={() => onStatusChange(slot.id, "planned")}
                        >
                            Plan
                        </button>
                    )}
                </div>
            )}
        </div>
    );
}
