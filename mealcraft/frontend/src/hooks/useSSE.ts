import {useCallback, useRef, useState} from "react";
import {apiPostStream} from "@/api/client";

interface UseSSEOptions<T> {
    onChunk?: (data: T) => void;
    onComplete?: (data: T | null) => void;
    onError?: (err: Error) => void;
}

interface UseSSEReturn<T> {
    data: T | null;
    isStreaming: boolean;
    error: Error | null;
    start: (path: string, body: unknown) => void;
    reset: () => void;
}

export function useSSE<T = unknown>(options: UseSSEOptions<T> = {}): UseSSEReturn<T> {
    const [data, setData] = useState<T | null>(null);
    const [isStreaming, setIsStreaming] = useState(false);
    const [error, setError] = useState<Error | null>(null);
    const abortRef = useRef(false);

    const reset = useCallback(() => {
        setData(null);
        setIsStreaming(false);
        setError(null);
        abortRef.current = false;
    }, []);

    const start = useCallback(
        (path: string, body: unknown) => {
            abortRef.current = false;
            setIsStreaming(true);
            setError(null);
            setData(null);

            apiPostStream(
                path,
                body,
                (rawData) => {
                    if (abortRef.current) return;
                    try {
                        const parsed = JSON.parse(rawData) as Record<string, unknown>;
                        if (parsed.complete && parsed.recipe) {
                            const complete = parsed.recipe as T;
                            setData(complete);
                            options.onComplete?.(complete);
                        } else if (parsed.partial) {
                            options.onChunk?.(parsed as T);
                        } else if (parsed.error) {
                            const err = new Error(parsed.error as string);
                            setError(err);
                            options.onError?.(err);
                        }
                    } catch {
                        // partial JSON during streaming is expected
                    }
                },
                () => {
                    if (!abortRef.current) {
                        setIsStreaming(false);
                    }
                },
                (err) => {
                    if (!abortRef.current) {
                        setError(err);
                        setIsStreaming(false);
                        options.onError?.(err);
                    }
                }
            );
        },
        [options]
    );

    return {data, isStreaming, error, start, reset};
}
