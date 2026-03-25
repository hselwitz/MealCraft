import {Calendar, Clock, Coffee, Zap} from "lucide-react";
import {useGeneratePrepPlan, usePlans} from "@/hooks/useApi";
import {useLocalStorage} from "@/hooks/useLocalStorage";
import type {PrepPlan, PrepTask} from "@/types";
import {Button} from "@/components/ui/button";
import {Badge} from "@/components/ui/badge";
import {Card, CardBody, CardHeader} from "@/components/ui/card";

export function PrepDashboard() {
    const {data: plans} = usePlans();
    const generatePrep = useGeneratePrepPlan();

    const activePlan = plans?.find((p) => p.status === "active" || p.status === "draft");

    // Stable keys — store planId alongside data so we can validate on load
    const [storedPrep, setStoredPrep] = useLocalStorage<{ planId: string; plan: PrepPlan } | null>(
        "mealcraft:prep", null
    );
    const [storedTasks, setStoredTasks] = useLocalStorage<{ planId: string; tasks: string[] } | null>(
        "mealcraft:prep-tasks", null
    );
    const prepPlan = storedPrep?.planId === activePlan?.id ? storedPrep.plan : null;
    const completedTaskNames = storedTasks?.planId === activePlan?.id ? storedTasks.tasks : [];
    const completedTasks = new Set(completedTaskNames);

    const handleGenerate = async () => {
        if (!activePlan) return;
        const result = await generatePrep.mutateAsync({
            planId: activePlan.id,
            timeWindows: ["Sunday afternoon 2-4pm", "Wednesday evening 6-7pm"],
        });
        setStoredPrep({planId: activePlan.id, plan: result});
        setStoredTasks({planId: activePlan.id, tasks: []});
    };

    const toggleTask = (taskName: string) => {
        if (!activePlan) return;
        const next = new Set(completedTasks);
        if (next.has(taskName)) next.delete(taskName);
        else next.add(taskName);
        setStoredTasks({planId: activePlan.id, tasks: [...next]});
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
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">Prep Dashboard</h1>
                    {activePlan && (
                        <p className="text-sm text-gray-500 mt-1">
                            {activePlan.name}
                        </p>
                    )}
                </div>

                <Button
                    onClick={handleGenerate}
                    loading={generatePrep.isPending}
                    disabled={!activePlan}
                >
                    Generate Prep Plan
                </Button>
            </div>

            {!activePlan && (
                <div className="text-center py-16 text-gray-400">
                    <Calendar size={48} className="mx-auto mb-3 opacity-30"/>
                    <p>No active plan found. Create and generate a meal plan first.</p>
                </div>
            )}

            {prepPlan && (
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
                                    <h3 className="font-semibold text-gray-800">{group}</h3>
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
                            {task.task_name}
                          </span>
                                                    <span
                                                        className="text-xs text-gray-400">{task.duration_min}min</span>
                                                    <Badge variant={task.is_active ? "yellow" : "blue"}>
                                                        {task.is_active ? "active" : "passive"}
                                                    </Badge>
                                                </div>
                                                {task.depends_on.length > 0 && (
                                                    <p className="text-xs text-gray-400 mt-0.5">
                                                        After: {task.depends_on.join(", ")}
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
