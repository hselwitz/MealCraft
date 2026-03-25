import {useState} from "react";
import {CheckCircle2, ShoppingCart} from "lucide-react";
import {GroceryListSkeleton} from "@/components/ui/skeleton";
import {useGenerateGroceryList, useGroceryList, usePlans, useToggleGroceryItem} from "@/hooks/useApi";
import {useLocalStorage} from "@/hooks/useLocalStorage";
import {useSettings} from "@/hooks/useSettings";
import {AmazonFreshModal} from "@/components/AmazonFreshModal";
import type {GroceryItem, StoreSection} from "@/types";
import {Button} from "@/components/ui/button";
import {Badge} from "@/components/ui/badge";
import {Card, CardBody, CardHeader} from "@/components/ui/card";

const SECTION_LABELS: Record<StoreSection, string> = {
    produce: "🥦 Produce",
    meat: "🥩 Meat & Seafood",
    dairy: "🥛 Dairy & Eggs",
    bakery: "🍞 Bakery",
    pantry: "🥫 Pantry & Dry Goods",
    frozen: "🧊 Frozen",
    other: "📦 Other",
};

const SECTION_ORDER: StoreSection[] = ["produce", "meat", "dairy", "bakery", "pantry", "frozen", "other"];

export function GroceryList() {
    const {data: plans} = usePlans();
    const [settings] = useSettings();
    const generateList = useGenerateGroceryList();
    const toggleItem = useToggleGroceryItem();

    const activePlan = plans?.find((p) => p.status === "active" || p.status === "draft");

    // Store {planId, listId} under a stable key so the hook never re-initializes on load
    const [stored, setStored] = useLocalStorage<{ planId: string; listId: string } | null>(
        "mealcraft:grocery", null
    );
    // @ts-ignore
    const groceryListId = stored?.planId === activePlan?.id ? stored.listId : null;

    const {data: groceryList, isLoading} = useGroceryList(groceryListId ?? undefined);

    const handleGenerate = async () => {
        if (!activePlan) return;
        const result = await generateList.mutateAsync({
            planId: activePlan.id,
            pantryStaples: settings.pantryStaples,
        });
        setStored({planId: activePlan.id, listId: result.grocery_list_id});
    };

    const handleToggle = async (item: GroceryItem) => {
        if (!groceryListId) return;
        await toggleItem.mutateAsync({
            listId: groceryListId,
            itemId: item.id,
            checked: !item.checked,
        });
    };

    // Group by section
    const itemsBySection = groceryList?.items.reduce<Record<string, GroceryItem[]>>(
        (acc, item) => {
            const section = item.store_section as StoreSection;
            if (!acc[section]) acc[section] = [];
            acc[section].push(item);
            return acc;
        },
        {}
    );

    const [showAmazon, setShowAmazon] = useState(false);

    const checkedCount = groceryList?.items.filter((i) => i.checked).length ?? 0;
    const totalCount = groceryList?.items.length ?? 0;
    const uncheckedCount = totalCount - checkedCount;

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">Grocery List</h1>
                    {groceryList && (
                        <p className="text-sm text-gray-500 mt-1">
                            {checkedCount}/{totalCount} items checked
                        </p>
                    )}
                </div>

                <div className="flex items-center gap-2">
                    {uncheckedCount > 0 && (
                        <button
                            onClick={() => setShowAmazon(true)}
                            className="flex items-center gap-2 px-3 py-2 rounded-lg bg-orange-500 hover:bg-orange-600 text-white text-sm font-medium transition-colors"
                        >
                            <ShoppingCart size={15}/>
                            Shop on Amazon Fresh
                            <span className="bg-orange-400 text-white text-xs font-bold px-1.5 py-0.5 rounded-full">
                                {uncheckedCount}
                            </span>
                        </button>
                    )}
                    <Button
                        onClick={handleGenerate}
                        loading={generateList.isPending}
                        disabled={!activePlan}
                        variant="outline"
                        className="flex items-center gap-2"
                    >
                        <ShoppingCart size={16}/>
                        {groceryList ? "Regenerate" : "Generate List"}
                    </Button>
                </div>
            </div>

            {!activePlan && (
                <div className="text-center py-16 text-gray-400">
                    <ShoppingCart size={48} className="mx-auto mb-3 opacity-30"/>
                    <p>No active plan found. Create a meal plan first.</p>
                </div>
            )}

            {isLoading && <GroceryListSkeleton/>}

            {groceryList && (
                <>
                    {/* Progress */}
                    {totalCount > 0 && (
                        <div>
                            <div className="flex justify-between text-sm text-gray-500 mb-1">
                                <span>Shopping progress</span>
                                <span>{Math.round((checkedCount / totalCount) * 100)}%</span>
                            </div>
                            <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                                <div
                                    className="h-full bg-primary-500 rounded-full transition-all"
                                    style={{width: `${(checkedCount / totalCount) * 100}%`}}
                                />
                            </div>
                        </div>
                    )}

                    {/* Sections */}
                    <div className="space-y-4">
                        {SECTION_ORDER.filter((s) => itemsBySection?.[s]?.length).map((section) => {
                            const items = itemsBySection?.[section] ?? [];
                            const allChecked = items.every((i) => i.checked);

                            return (
                                <Card key={section}>
                                    <CardHeader>
                                        <div className="flex items-center justify-between">
                                            <h3 className="font-semibold text-gray-800">
                                                {SECTION_LABELS[section]}
                                            </h3>
                                            <Badge variant={allChecked ? "green" : "gray"}>
                                                {items.filter((i) => i.checked).length}/{items.length}
                                            </Badge>
                                        </div>
                                    </CardHeader>
                                    <CardBody className="py-2 space-y-1">
                                        {items.map((item) => (
                                            <div
                                                key={item.id}
                                                className={[
                                                    "flex items-center gap-3 px-2 py-1.5 rounded-lg cursor-pointer transition-colors",
                                                    item.checked ? "bg-gray-50" : "hover:bg-gray-50",
                                                ].join(" ")}
                                                onClick={() => handleToggle(item)}
                                            >
                                                <input
                                                    type="checkbox"
                                                    checked={item.checked}
                                                    onChange={() => handleToggle(item)}
                                                    className="h-4 w-4 rounded border-gray-300 text-primary-600"
                                                    onClick={(e) => e.stopPropagation()}
                                                />
                                                <span
                                                    className={[
                                                        "flex-1 text-sm",
                                                        item.checked ? "line-through text-gray-400" : "text-gray-700",
                                                    ].join(" ")}
                                                >
                          {item.ingredient_name}
                        </span>
                                                <span
                                                    className={[
                                                        "text-sm font-medium",
                                                        item.checked ? "text-gray-300" : "text-gray-600",
                                                    ].join(" ")}
                                                >
                          {item.quantity % 1 === 0 ? item.quantity : item.quantity.toFixed(2)}{" "}
                                                    {item.unit}
                        </span>
                                                {item.checked && (
                                                    <CheckCircle2 size={16} className="text-green-400"/>
                                                )}
                                            </div>
                                        ))}
                                    </CardBody>
                                </Card>
                            );
                        })}
                    </div>

                    {checkedCount === totalCount && totalCount > 0 && (
                        <div className="text-center py-6">
                            <div className="text-4xl mb-2">🛒✅</div>
                            <p className="text-gray-700 font-medium">All items checked off! Happy cooking!</p>
                        </div>
                    )}
                </>
            )}

            {showAmazon && groceryList && (
                <AmazonFreshModal
                    items={groceryList.items}
                    onClose={() => setShowAmazon(false)}
                    onCheck={(item) => handleToggle(item)}
                />
            )}
        </div>
    );
}
