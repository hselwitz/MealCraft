export function Skeleton({className = ""}: { className?: string }) {
    return (
        <div className={`animate-pulse rounded-md bg-gray-200 ${className}`}/>
    );
}

export function RecipeCardSkeleton() {
    return (
        <div className="rounded-xl border border-gray-200 bg-white overflow-hidden">
            <Skeleton className="h-1 rounded-none"/>
            <div className="p-4 space-y-3">
                <Skeleton className="h-4 w-3/4"/>
                <Skeleton className="h-3 w-full"/>
                <Skeleton className="h-3 w-5/6"/>
                <div className="flex gap-3 pt-1">
                    <Skeleton className="h-3 w-14"/>
                    <Skeleton className="h-3 w-10"/>
                    <Skeleton className="h-3 w-16"/>
                </div>
                <div className="flex gap-1.5 pt-1">
                    <Skeleton className="h-5 w-12 rounded-full"/>
                    <Skeleton className="h-5 w-16 rounded-full"/>
                    <Skeleton className="h-5 w-14 rounded-full"/>
                </div>
            </div>
        </div>
    );
}

export function GroceryListSkeleton() {
    return (
        <div className="space-y-4">
            {[1, 2, 3].map((i) => (
                <div key={i} className="rounded-xl border border-gray-200 bg-white p-4 space-y-3">
                    <Skeleton className="h-4 w-32"/>
                    {[1, 2, 3, 4].map((j) => (
                        <div key={j} className="flex items-center justify-between">
                            <div className="flex items-center gap-3">
                                <Skeleton className="h-4 w-4 rounded"/>
                                <Skeleton className="h-3 w-32"/>
                            </div>
                            <Skeleton className="h-3 w-16"/>
                        </div>
                    ))}
                </div>
            ))}
        </div>
    );
}

export function LeftoverCardSkeleton() {
    return (
        <div className="rounded-xl border border-gray-200 bg-white overflow-hidden">
            <Skeleton className="h-1.5 rounded-none"/>
            <div className="p-4 space-y-3">
                <div className="flex items-start justify-between">
                    <Skeleton className="h-4 w-40"/>
                    <Skeleton className="h-5 w-20 rounded-full"/>
                </div>
                <Skeleton className="h-3 w-24"/>
                <Skeleton className="h-3 w-32"/>
                <Skeleton className="h-3 w-28"/>
                <div className="flex gap-2 pt-1">
                    <Skeleton className="h-7 flex-1 rounded-lg"/>
                    <Skeleton className="h-7 flex-1 rounded-lg"/>
                </div>
            </div>
        </div>
    );
}
