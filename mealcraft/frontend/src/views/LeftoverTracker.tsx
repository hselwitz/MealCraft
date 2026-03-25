import {useState} from "react";
import {AlertTriangle, CheckCircle, Lightbulb, Refrigerator, Trash2} from "lucide-react";
import {LeftoverCardSkeleton} from "@/components/ui/skeleton";
import {useLeftovers, useLeftoverSuggestions, useUpdateLeftover} from "@/hooks/useApi";
import {Button} from "@/components/ui/button";
import {Badge} from "@/components/ui/badge";
import {Card, CardBody} from "@/components/ui/card";

function getExpiryStatus(expiryDate: string): { label: string; variant: "green" | "yellow" | "red"; daysLeft: number } {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const expiry = new Date(expiryDate + "T00:00:00");
    const daysLeft = Math.ceil((expiry.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));

    if (daysLeft < 0) return {label: "Expired", variant: "red", daysLeft};
    if (daysLeft === 0) return {label: "Expires today", variant: "red", daysLeft};
    if (daysLeft === 1) return {label: "Expires tomorrow", variant: "yellow", daysLeft};
    if (daysLeft <= 2) return {label: `${daysLeft} days left`, variant: "yellow", daysLeft};
    return {label: `${daysLeft} days left`, variant: "green", daysLeft};
}

export function LeftoverTracker() {
    const {data: leftovers, isLoading, refetch} = useLeftovers("available");
    const updateLeftover = useUpdateLeftover();
    const getSuggestions = useLeftoverSuggestions();
    const [suggestions, setSuggestions] = useState<string[]>([]);
    const [showSuggestions, setShowSuggestions] = useState(false);

    const handleMark = async (id: string, status: "used" | "discarded") => {
        await updateLeftover.mutateAsync({id, body: {status}});
    };

    const handleGetSuggestions = async () => {
        const result = await getSuggestions.mutateAsync();
        setSuggestions(result.suggestions);
        setShowSuggestions(true);
    };

    // Sort by expiry (soonest first)
    const sorted = [...(leftovers ?? [])].sort((a, b) => {
        const dA = getExpiryStatus(a.expiry_date).daysLeft;
        const dB = getExpiryStatus(b.expiry_date).daysLeft;
        return dA - dB;
    });

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">Leftover Tracker</h1>
                    <p className="text-sm text-gray-500 mt-1">
                        {sorted.length} item{sorted.length !== 1 ? "s" : ""} available
                    </p>
                </div>

                <Button
                    variant="outline"
                    onClick={handleGetSuggestions}
                    loading={getSuggestions.isPending}
                    disabled={sorted.length === 0}
                    className="flex items-center gap-2"
                >
                    <Lightbulb size={16}/>
                    Get Suggestions
                </Button>
            </div>

            {/* LLM Suggestions */}
            {showSuggestions && suggestions.length > 0 && (
                <Card className="border-yellow-200 bg-yellow-50">
                    <CardBody>
                        <div className="flex items-start gap-2">
                            <Lightbulb size={20} className="text-yellow-500 shrink-0 mt-0.5"/>
                            <div>
                                <h3 className="font-semibold text-gray-800 mb-2">Leftover Use Suggestions</h3>
                                <ul className="space-y-1.5">
                                    {suggestions.map((s, i) => (
                                        <li key={i} className="text-sm text-gray-700 flex gap-2">
                                            <span className="text-yellow-500">•</span>
                                            <span>{s}</span>
                                        </li>
                                    ))}
                                </ul>
                            </div>
                            <button
                                className="ml-auto text-gray-400 hover:text-gray-600 shrink-0"
                                onClick={() => setShowSuggestions(false)}
                            >
                                ×
                            </button>
                        </div>
                    </CardBody>
                </Card>
            )}

            {isLoading && (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                    {Array.from({length: 3}).map((_, i) => <LeftoverCardSkeleton key={i}/>)}
                </div>
            )}

            {!isLoading && sorted.length === 0 && (
                <div className="text-center py-16 text-gray-400">
                    <Refrigerator size={48} className="mx-auto mb-3 opacity-30"/>
                    <p>No leftovers tracked yet.</p>
                    <p className="text-sm mt-1">Mark meals as cooked to add leftovers.</p>
                </div>
            )}

            {/* Leftover cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {sorted.map((lv) => {
                    const expiry = getExpiryStatus(lv.expiry_date);
                    return (
                        <Card key={lv.id} className="overflow-hidden">
                            {/* Expiry indicator strip */}
                            <div
                                className={[
                                    "h-1.5",
                                    expiry.variant === "green"
                                        ? "bg-green-400"
                                        : expiry.variant === "yellow"
                                            ? "bg-yellow-400"
                                            : "bg-red-400",
                                ].join(" ")}
                            />
                            <CardBody>
                                <div className="flex items-start justify-between gap-2 mb-2">
                                    <h3 className="font-semibold text-gray-900 leading-tight">
                                        {lv.recipe?.title ?? "Unknown dish"}
                                    </h3>
                                    <Badge variant={expiry.variant} className="shrink-0">
                                        {expiry.variant === "red" && expiry.daysLeft < 0 ? (
                                            <AlertTriangle size={10} className="mr-1"/>
                                        ) : null}
                                        {expiry.label}
                                    </Badge>
                                </div>

                                <div className="text-sm text-gray-500 space-y-1 mb-3">
                                    <p>{lv.remaining_servings} serving{lv.remaining_servings !== 1 ? "s" : ""} left</p>
                                    <p>Stored: {new Date(lv.stored_date + "T12:00:00").toLocaleDateString()}</p>
                                    <p>
                                        Expires:{" "}
                                        {new Date(lv.expiry_date + "T12:00:00").toLocaleDateString()}
                                    </p>
                                </div>

                                <div className="flex gap-2">
                                    <button
                                        className="flex-1 flex items-center justify-center gap-1.5 py-1.5 rounded-lg text-xs font-medium bg-green-100 text-green-700 hover:bg-green-200 transition-colors"
                                        onClick={() => handleMark(lv.id, "used")}
                                    >
                                        <CheckCircle size={13}/>
                                        Used
                                    </button>
                                    <button
                                        className="flex-1 flex items-center justify-center gap-1.5 py-1.5 rounded-lg text-xs font-medium bg-red-100 text-red-600 hover:bg-red-200 transition-colors"
                                        onClick={() => handleMark(lv.id, "discarded")}
                                    >
                                        <Trash2 size={13}/>
                                        Discard
                                    </button>
                                </div>
                            </CardBody>
                        </Card>
                    );
                })}
            </div>
        </div>
    );
}
