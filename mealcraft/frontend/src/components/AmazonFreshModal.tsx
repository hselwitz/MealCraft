import {CheckCircle2, ExternalLink, ShoppingBasket, X} from "lucide-react";
import type {GroceryItem, StoreSection} from "@/types";

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

function amazonFreshUrl(ingredientName: string) {
    return `https://www.amazon.com/s?k=${encodeURIComponent(ingredientName)}&i=amazonfresh`;
}

interface Props {
    items: GroceryItem[];
    onClose: () => void;
    onCheck: (item: GroceryItem) => void;
}

export function AmazonFreshModal({items, onClose, onCheck}: Props) {
    const unchecked = items.filter((i) => !i.checked);
    const allDone = unchecked.length === 0;

    const bySection = items.reduce<Record<string, GroceryItem[]>>((acc, item) => {
        if (item.checked) return acc;
        const s = item.store_section as StoreSection;
        if (!acc[s]) acc[s] = [];
        acc[s].push(item);
        return acc;
    }, {});

    return (
        <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center">
            {/* Backdrop */}
            <div
                className="absolute inset-0 bg-black/40 backdrop-blur-sm"
                onClick={onClose}
            />

            {/* Panel */}
            <div
                className="relative w-full sm:max-w-lg max-h-[85vh] flex flex-col bg-white sm:rounded-2xl rounded-t-2xl shadow-2xl overflow-hidden">
                {/* Header */}
                <div className="flex items-center justify-between px-5 py-4 bg-orange-500 text-white shrink-0">
                    <div className="flex items-center gap-2">
                        <ShoppingBasket size={20}/>
                        <div>
                            <h2 className="font-semibold text-base leading-tight">Shop on Amazon Fresh</h2>
                            <p className="text-orange-100 text-xs">
                                {allDone ? "All items checked off!" : `${unchecked.length} item${unchecked.length !== 1 ? "s" : ""} remaining`}
                            </p>
                        </div>
                    </div>
                    <button
                        onClick={onClose}
                        className="p-1.5 rounded-lg hover:bg-orange-600 transition-colors"
                    >
                        <X size={18}/>
                    </button>
                </div>

                {/* Body */}
                <div className="overflow-y-auto flex-1 px-4 py-3">
                    {allDone ? (
                        <div className="flex flex-col items-center justify-center py-12 text-center">
                            <div className="text-5xl mb-3">🛒✅</div>
                            <p className="font-medium text-gray-800">All done!</p>
                            <p className="text-sm text-gray-500 mt-1">Everything's been added to your cart.</p>
                        </div>
                    ) : (
                        <div className="space-y-4">
                            <p className="text-xs text-gray-400 pb-1">
                                Tap an item to open Amazon Fresh and mark it checked.
                            </p>
                            {SECTION_ORDER.filter((s) => bySection[s]?.length).map((section) => (
                                <div key={section}>
                                    <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1.5">
                                        {SECTION_LABELS[section]}
                                    </h3>
                                    <div className="space-y-1">
                                        {bySection[section].map((item) => (
                                            <a
                                                key={item.id}
                                                href={amazonFreshUrl(item.ingredient_name)}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                onClick={() => onCheck(item)}
                                                className="flex items-center justify-between gap-3 px-3 py-2.5 rounded-xl border border-gray-100 hover:border-orange-200 hover:bg-orange-50 transition-colors group"
                                            >
                                                <div className="flex items-center gap-2.5 min-w-0">
                                                    <CheckCircle2
                                                        size={16}
                                                        className="shrink-0 text-gray-200 group-hover:text-orange-400 transition-colors"
                                                    />
                                                    <span className="text-sm text-gray-800 truncate">
                                                        {item.ingredient_name}
                                                    </span>
                                                </div>
                                                <div className="flex items-center gap-2 shrink-0">
                                                    <span className="text-xs text-gray-400">
                                                        {item.quantity % 1 === 0 ? item.quantity : item.quantity.toFixed(2)} {item.unit}
                                                    </span>
                                                    <ExternalLink
                                                        size={12}
                                                        className="text-gray-300 group-hover:text-orange-400 transition-colors"
                                                    />
                                                </div>
                                            </a>
                                        ))}
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
