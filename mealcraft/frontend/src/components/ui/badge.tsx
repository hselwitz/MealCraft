import React from "react";

type BadgeVariant = "green" | "yellow" | "red" | "blue" | "gray" | "purple";

interface BadgeProps {
    children: React.ReactNode;
    variant?: BadgeVariant;
    className?: string;
}

const variantClasses: Record<BadgeVariant, string> = {
    green: "bg-green-100 text-green-800",
    yellow: "bg-yellow-100 text-yellow-800",
    red: "bg-red-100 text-red-800",
    blue: "bg-blue-100 text-blue-800",
    gray: "bg-gray-100 text-gray-700",
    purple: "bg-purple-100 text-purple-800",
};

export function Badge({children, variant = "gray", className = ""}: BadgeProps) {
    return (
        <span
            className={[
                "inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium",
                variantClasses[variant],
                className,
            ].join(" ")}
        >
      {children}
    </span>
    );
}
