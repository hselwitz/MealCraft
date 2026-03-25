import React from "react";

interface CardProps {
    children: React.ReactNode;
    className?: string;
    onClick?: () => void;
}

export function Card({children, className = "", onClick}: CardProps) {
    return (
        <div
            onClick={onClick}
            className={[
                "bg-white rounded-xl border border-gray-200 shadow-sm",
                onClick ? "cursor-pointer hover:shadow-md transition-shadow" : "",
                className,
            ].join(" ")}
        >
            {children}
        </div>
    );
}

export function CardHeader({children, className = ""}: { children: React.ReactNode; className?: string }) {
    return (
        <div className={`px-4 py-3 border-b border-gray-100 ${className}`}>
            {children}
        </div>
    );
}

export function CardBody({children, className = ""}: { children: React.ReactNode; className?: string }) {
    return <div className={`px-4 py-3 ${className}`}>{children}</div>;
}

export function CardFooter({children, className = ""}: { children: React.ReactNode; className?: string }) {
    return (
        <div className={`px-4 py-3 border-t border-gray-100 ${className}`}>
            {children}
        </div>
    );
}
