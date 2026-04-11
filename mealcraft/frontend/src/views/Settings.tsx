import {useState} from "react";
import {CheckCircle2, Settings2, X} from "lucide-react";
import {type AppSettings, DEFAULT_SETTINGS, useSettings} from "@/hooks/useSettings";
import {Button} from "@/components/ui/button";
import {Card, CardBody, CardHeader} from "@/components/ui/card";

const DIFFICULTY_OPTIONS: { value: AppSettings["maxDifficulty"]; label: string; desc: string }[] = [
    {value: "easy", label: "Easy", desc: "Simple techniques, minimal prep, 30 min or less"},
    {value: "medium", label: "Medium", desc: "Some skill required, up to 45 min active time"},
    {value: "hard", label: "Hard", desc: "Advanced techniques, longer prep allowed"},
];

const OVERLAP_OPTIONS: { value: AppSettings["ingredientOverlap"]; label: string; desc: string }[] = [
    {
        value: "low",
        label: "Variety",
        desc: "Different ingredients each day — more interesting but a longer shopping list"
    },
    {value: "medium", label: "Balanced", desc: "~30% overlap — some shared staples with daily variety"},
    {value: "high", label: "Efficient", desc: "Maximize reuse — fewer unique items to buy, shorter shopping list"},
];

function TagInput({
                      values,
                      onChange,
                      placeholder,
                  }: {
    values: string[];
    onChange: (v: string[]) => void;
    placeholder: string;
}) {
    const [input, setInput] = useState("");

    const add = () => {
        const trimmed = input.trim();
        if (trimmed && !values.includes(trimmed)) {
            onChange([...values, trimmed]);
        }
        setInput("");
    };

    return (
        <div className="space-y-2">
            <div className="flex gap-2">
                <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), add())}
                    placeholder={placeholder}
                    className="flex-1 text-sm border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
                <Button variant="outline" size="sm" onClick={add} disabled={!input.trim()}>
                    Add
                </Button>
            </div>
            {values.length > 0 && (
                <div className="flex flex-wrap gap-1.5">
                    {values.map((v) => (
                        <span
                            key={v}
                            className="inline-flex items-center gap-1 bg-primary-50 text-primary-700 text-xs font-medium px-2.5 py-1 rounded-full"
                        >
                            {v}
                            <button
                                onClick={() => onChange(values.filter((x) => x !== v))}
                                className="hover:text-primary-900"
                            >
                                <X size={11}/>
                            </button>
                        </span>
                    ))}
                </div>
            )}
        </div>
    );
}

export function Settings() {
    const [settings, setSettings] = useSettings();
    const [saved, setSaved] = useState(false);

    const update = <K extends keyof AppSettings>(key: K, value: AppSettings[K]) => {
        setSettings((prev) => ({...prev, [key]: value}));
        setSaved(false);
    };

    const handleSave = () => {
        // Settings are already persisted live via useLocalStorage,
        // but give the user explicit confirmation.
        setSaved(true);
        setTimeout(() => setSaved(false), 2500);
    };

    const handleReset = () => {
        setSettings(DEFAULT_SETTINGS);
        setSaved(false);
    };

    return (
        <div className="max-w-2xl space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
                        <Settings2 size={24}/> Settings
                    </h1>
                    <p className="text-sm text-gray-500 mt-1">
                        These preferences are applied the next time you generate a plan.
                    </p>
                </div>
                <div className="flex items-center gap-2">
                    <Button variant="ghost" size="sm" onClick={handleReset}>
                        Reset to defaults
                    </Button>
                    <Button size="sm" onClick={handleSave} className="flex items-center gap-1.5">
                        {saved ? <><CheckCircle2 size={14}/> Saved</> : "Save"}
                    </Button>
                </div>
            </div>

            {/* Recipe Complexity */}
            <Card>
                <CardHeader>
                    <h2 className="font-semibold text-gray-900">Recipe Complexity</h2>
                    <p className="text-sm text-gray-500">Sets the difficulty ceiling for generated recipes.</p>
                </CardHeader>
                <CardBody className="space-y-2 pt-0">
                    {DIFFICULTY_OPTIONS.map((opt) => (
                        <label
                            key={opt.value}
                            className={[
                                "flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-colors",
                                settings.maxDifficulty === opt.value
                                    ? "border-primary-400 bg-primary-50"
                                    : "border-gray-200 hover:bg-gray-50",
                            ].join(" ")}
                        >
                            <input
                                type="radio"
                                name="difficulty"
                                value={opt.value}
                                checked={settings.maxDifficulty === opt.value}
                                onChange={() => update("maxDifficulty", opt.value)}
                                className="mt-0.5 text-primary-600"
                            />
                            <div>
                                <div className="text-sm font-medium text-gray-800">{opt.label}</div>
                                <div className="text-xs text-gray-500">{opt.desc}</div>
                            </div>
                        </label>
                    ))}
                </CardBody>
            </Card>

            {/* Shopping List Scope */}
            <Card>
                <CardHeader>
                    <h2 className="font-semibold text-gray-900">Shopping List Scope</h2>
                    <p className="text-sm text-gray-500">
                        Controls how much the planner reuses the same ingredients across meals.
                        Higher overlap means a shorter, more focused shopping list.
                    </p>
                </CardHeader>
                <CardBody className="space-y-2 pt-0">
                    {OVERLAP_OPTIONS.map((opt) => (
                        <label
                            key={opt.value}
                            className={[
                                "flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-colors",
                                settings.ingredientOverlap === opt.value
                                    ? "border-primary-400 bg-primary-50"
                                    : "border-gray-200 hover:bg-gray-50",
                            ].join(" ")}
                        >
                            <input
                                type="radio"
                                name="overlap"
                                value={opt.value}
                                checked={settings.ingredientOverlap === opt.value}
                                onChange={() => update("ingredientOverlap", opt.value)}
                                className="mt-0.5 text-primary-600"
                            />
                            <div>
                                <div className="text-sm font-medium text-gray-800">{opt.label}</div>
                                <div className="text-xs text-gray-500">{opt.desc}</div>
                            </div>
                        </label>
                    ))}
                </CardBody>
            </Card>

            {/* Meal Prep Focus */}
            <Card>
                <CardBody className="pt-4">
                    <label className="flex items-start gap-3 cursor-pointer">
                        <input
                            type="checkbox"
                            checked={settings.mealPrepFocus}
                            onChange={(e) => update("mealPrepFocus", e.target.checked)}
                            className="mt-0.5 accent-primary-600 w-4 h-4 shrink-0"
                        />
                        <div>
                            <div className="text-sm font-semibold text-gray-800">Meal prep focus</div>
                            <div className="text-xs text-gray-500 mt-0.5">
                                Plan around 2–3 batch-cooked base components prepared once. All other meals
                                assemble in ≤15 min. Meals may repeat — variety comes from sauces and toppings,
                                not new ingredients.
                            </div>
                        </div>
                    </label>
                </CardBody>
            </Card>

            {/* Portions & Nutrition */}
            <Card>
                <CardHeader>
                    <h2 className="font-semibold text-gray-900">Portions & Nutrition</h2>
                </CardHeader>
                <CardBody className="space-y-4 pt-0">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            Default servings per meal
                        </label>
                        <div className="flex items-center gap-3">
                            <input
                                type="range"
                                min={1}
                                max={6}
                                value={settings.defaultServings}
                                onChange={(e) => update("defaultServings", Number(e.target.value))}
                                className="w-40 accent-primary-600"
                            />
                            <span className="text-sm font-semibold text-gray-800 w-16">
                                {settings.defaultServings} {settings.defaultServings === 1 ? "person" : "people"}
                            </span>
                        </div>
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            Daily calorie target <span className="text-gray-400">(soft guide)</span>
                        </label>
                        <div className="flex items-center gap-3">
                            <input
                                type="range"
                                min={1500}
                                max={4000}
                                step={100}
                                value={settings.calorieTarget}
                                onChange={(e) => update("calorieTarget", Number(e.target.value))}
                                className="w-40 accent-primary-600"
                            />
                            <span className="text-sm font-semibold text-gray-800 w-20">
                                {settings.calorieTarget.toLocaleString()} kcal
                            </span>
                        </div>
                    </div>
                </CardBody>
            </Card>

            {/* Pantry Staples */}
            <Card>
                <CardHeader>
                    <h2 className="font-semibold text-gray-900">Pantry Staples</h2>
                    <p className="text-sm text-gray-500">
                        Items always on hand — excluded from the grocery list.
                    </p>
                </CardHeader>
                <CardBody className="pt-0">
                    <TagInput
                        values={settings.pantryStaples}
                        onChange={(v) => update("pantryStaples", v)}
                        placeholder="e.g. garlic, butter, soy sauce…"
                    />
                </CardBody>
            </Card>

            {/* Cuisine & Dietary */}
            <Card>
                <CardHeader>
                    <h2 className="font-semibold text-gray-900">Cuisine & Dietary</h2>
                    <p className="text-sm text-gray-500">Applied as soft preferences in the planning prompt.</p>
                </CardHeader>
                <CardBody className="space-y-4 pt-0">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            Cuisine preferences
                        </label>
                        <TagInput
                            values={settings.cuisinePreferences}
                            onChange={(v) => update("cuisinePreferences", v)}
                            placeholder="e.g. Mediterranean, Japanese, Mexican…"
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            Dietary restrictions
                        </label>
                        <TagInput
                            values={settings.dietaryRestrictions}
                            onChange={(v) => update("dietaryRestrictions", v)}
                            placeholder="e.g. gluten-free, no pork, dairy-free…"
                        />
                    </div>
                </CardBody>
            </Card>
        </div>
    );
}
