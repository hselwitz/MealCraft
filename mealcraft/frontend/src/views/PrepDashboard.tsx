import {KitchenArt} from "@/components/KitchenArt";
import {Link} from "react-router-dom";
import {usePlanningWindow} from "@/hooks/usePlanningWindow";
import {WorkflowBar} from "@/components/WorkflowBar";
import {Calendar, Clock, Coffee, Zap} from "lucide-react";
import {useCurrentPrepPlan, useGeneratePrepPlan, usePatchPrepPlan, usePlans} from "@/hooks/useApi";
import type {PrepTask} from "@/types";
import {Button} from "@/components/ui/button";
import {Badge} from "@/components/ui/badge";
import {Card, CardBody, CardHeader} from "@/components/ui/card";

export function PrepDashboard() {
    const {window, valid} = usePlanningWindow();
    const {data: plans} = usePlans();
    const generatePrep = useGeneratePrepPlan();
    const patchPrep = usePatchPrepPlan();

    const activePlan = plans?.find((p) => p.status === "active" || p.status === "draft");

    const {data: prepPlan} = useCurrentPrepPlan(valid ? activePlan?.id : undefined, window);
    const completedTasks = new Set(prepPlan?.completed_tasks ?? []);

    const handleGenerate = async () => {
        if (!activePlan) return;
        generatePrep.mutate({planId: activePlan.id, window});
    };

    const toggleTask = async (taskName: string) => {
        if (!activePlan) return;
        const next = new Set(completedTasks);
        if (next.has(taskName)) next.delete(taskName);
        else next.add(taskName);
        await patchPrep.mutateAsync({planId: activePlan.id, completedTasks: [...next]});
    };

    // Group tasks by batch_group
    const groupedTasks = prepPlan?.tasks.reduce<Record<string, PrepTask[]>>((acc, task) => {
        const key = task.batch_group ?? "Other Tasks";
        if (!acc[key]) acc[key] = [];
        acc[key].push(task);
        return acc;
    }, {});

    const completedCount = completedTasks.size;
    const totalCount = prepPlan?.tasks.length ?? 0;
    const totalTime = prepPlan?.tasks.reduce((sum, t) => sum + (t.duration_min ?? 1), 0) ?? 0;
    const doneTime = prepPlan?.tasks
        .filter((t) => completedTasks.has(t.task_name))
        .reduce((sum, t) => sum + (t.duration_min ?? 1), 0) ?? 0;
    const pct = totalTime > 0 ? (doneTime / totalTime) * 100 : 0;

    return (
        <div className="max-w-5xl mx-auto space-y-6">
            <WorkflowBar/>
            <div className="flex flex-wrap gap-4 items-center justify-between">
                <div className="flex items-center gap-3"><KitchenArt variant="prep" className="hidden sm:block w-20 shrink-0"/><div>
                    <h1 className="text-3xl kitchen-title text-gray-900">Prep your selected meals</h1>
                    {activePlan && (
                        <p className="text-sm text-gray-500 mt-1">
                            {activePlan.name}
                        </p>
                    )}
                </div></div>

                <Button
                    onClick={handleGenerate}
                    loading={generatePrep.isPending}
                    disabled={!activePlan || !valid}
                >
                    Coordinate Prep Session
                </Button>
            </div>

            {!activePlan && (
                <div className="text-center py-16 text-gray-400">
                    <Calendar size={48} className="mx-auto mb-3 opacity-30"/>
                    <p>No active plan found. Create and generate a meal plan first.</p>
                </div>
            )}

            {generatePrep.error && <p role="alert" className="text-sm text-red-600">{generatePrep.error.message}</p>}
            {patchPrep.error && <p role="alert" className="text-sm text-red-600">{patchPrep.error.message}</p>}
            {prepPlan?.stale && <p className="bg-yellow-50 border border-yellow-200 p-4 rounded-xl text-sm">Your meals, servings, or dates changed. Coordinate a fresh session for the current selection.</p>}
            {activePlan && !prepPlan && !generatePrep.isPending && <p className="text-sm text-gray-500">Pick multiple recipes in <Link to="/" className="underline">Plan</Link>, then coordinate their cooking, shared ingredients, and portioning here.</p>}
            {prepPlan && !prepPlan.stale && (
                <>
                    {/* Summary cards */}
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                        <Card>
                            <CardBody className="flex items-center gap-3">
                                <Zap size={24} className="text-yellow-500"/>
                                <div>
                                    <div className="text-2xl font-bold text-gray-900">{prepPlan.total_active_min}min
                                    </div>
                                    <div className="text-sm text-gray-500">Active cooking</div>
                                </div>
                            </CardBody>
                        </Card>
                        <Card>
                            <CardBody className="flex items-center gap-3">
                                <Coffee size={24} className="text-blue-400"/>
                                <div>
                                    <div className="text-2xl font-bold text-gray-900">{prepPlan.total_passive_min}min
                                    </div>
                                    <div className="text-sm text-gray-500">Passive time</div>
                                </div>
                            </CardBody>
                        </Card>
                        <Card>
                            <CardBody className="flex items-center gap-3">
                                <Clock size={24} className="text-green-500"/>
                                <div>
                                    <div className="text-2xl font-bold text-gray-900">
                                        {completedCount}/{totalCount}
                                    </div>
                                    <div className="text-sm text-gray-500">Tasks completed</div>
                                </div>
                            </CardBody>
                        </Card>
                    </div>

                    {prepPlan.session_elapsed_min && <p className="text-sm text-gray-600">Estimated session: {prepPlan.session_elapsed_min} minutes elapsed. Passive tasks can overlap.</p>}
                    {!!prepPlan.shared_components?.length && <p className="rounded-xl bg-primary-50 p-4 text-sm text-primary-900">Prep together: {prepPlan.shared_components.join(" · ")}</p>}
                    <Link to="/grocery" className="inline-block text-sm font-semibold text-primary-700">Shop for these meals →</Link>
                    {!!prepPlan.meal_finishes?.length && <section className="space-y-3"><h2 className="text-lg font-semibold">What remains at mealtime</h2>{prepPlan.meal_finishes.map(meal=><div key={meal.recipe_id} className="bg-white border rounded-xl p-4"><Link to={`/recipes/${meal.recipe_id}`} className="font-semibold">{meal.title}</Link><p className="text-xs text-primary-700 mt-1">About {meal.active_min} minutes hands-on</p><p className="text-sm text-gray-600 mt-2 whitespace-pre-wrap">{meal.instructions}</p></div>)}</section>}
                    {/* Recommended sessions */}
                    {prepPlan.recommended_sessions.length > 0 && (
                        <div>
                            <h2 className="text-lg font-semibold text-gray-900 mb-2">Recommended Sessions</h2>
                            <div className="flex flex-wrap gap-2">
                                {prepPlan.recommended_sessions.map((session) => (
                                    <Badge key={session} variant="blue" className="text-sm px-3 py-1">
                                        {session}
                                    </Badge>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Progress bar */}
                    {totalCount > 0 && (
                        <div>
                            <div className="flex justify-between text-sm text-gray-500 mb-1">
                                <span>Progress</span>
                                <span>{Math.round(pct)}%</span>
                            </div>
                            <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                                <div
                                    className="h-full bg-primary-500 rounded-full transition-all"
                                    style={{width: `${pct}%`}}
                                />
                            </div>
                        </div>
                    )}

                    {/* Task groups */}
                    <div className="space-y-4">
                        {Object.entries(groupedTasks ?? {}).map(([group, tasks]) => (
                            <Card key={group}>
                                <CardHeader>
                                    <h3 className="font-semibold text-gray-800">
                                        {group.replace(/_/g, " ").replace(/\w\S*/g, (w) => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase())}
                                    </h3>
                                </CardHeader>
                                <CardBody className="space-y-2 py-2">
                                    {tasks.map((task) => (
                                        <div
                                            key={task.task_name}
                                            className={[
                                                "flex items-start gap-3 p-2 rounded-lg cursor-pointer transition-colors",
                                                completedTasks.has(task.task_name)
                                                    ? "bg-green-50"
                                                    : "hover:bg-gray-50",
                                            ].join(" ")}
                                            onClick={() => toggleTask(task.task_name)}
                                        >
                                            <input
                                                type="checkbox"
                                                checked={completedTasks.has(task.task_name)}
                                                onChange={() => toggleTask(task.task_name)}
                                                className="mt-0.5 h-4 w-4 rounded border-gray-300 text-primary-600"
                                                onClick={(e) => e.stopPropagation()}
                                            />
                                            <div className="flex-1 min-w-0">
                                                <div className="flex items-center gap-2 flex-wrap">
                          <span
                              className={[
                                  "text-sm font-medium",
                                  completedTasks.has(task.task_name)
                                      ? "line-through text-gray-400"
                                      : "text-gray-800",
                              ].join(" ")}
                          >
                            {task.task_name.replace(/_/g, " ")}
                          </span>
                                                    <span
                                                        className="text-xs text-gray-400">{task.duration_min}min</span>
                                                    <Badge variant={task.is_active ? "yellow" : "blue"}>
                                                        {task.is_active ? "active" : "passive"}
                                                    </Badge>
                                                </div>
                                                {task.tip && (
                                                    <p className="text-xs text-blue-500 mt-0.5">{task.tip}</p>
                                                )}
                                                {task.depends_on.length > 0 && (
                                                    <p className="text-xs text-gray-400 mt-0.5">
                                                        After: {task.depends_on.map((d) => d.replace(/_/g, " ")).join(", ")}
                                                    </p>
                                                )}
                                            </div>
                                        </div>
                                    ))}
                                </CardBody>
                            </Card>
                        ))}
                    </div>
                </>
            )}
        </div>
    );
}
