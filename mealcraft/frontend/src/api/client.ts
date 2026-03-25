const BASE_URL = "/api";

export class ApiError extends Error {
    status: number;
    detail: string;

    constructor(status: number, detail: string) {
        super(detail);
        this.status = status;
        this.detail = detail;
    }
}

async function handleResponse<T>(res: Response): Promise<T> {
    if (!res.ok) {
        let detail = `HTTP ${res.status}`;
        try {
            const body = await res.json();
            detail = body.detail || body.title || detail;
        } catch {
            // ignore parse errors
        }
        throw new ApiError(res.status, detail);
    }
    return res.json() as Promise<T>;
}

export async function apiGet<T>(path: string, params?: Record<string, string>): Promise<T> {
    const url = new URL(`${BASE_URL}${path}`, window.location.origin);
    if (params) {
        Object.entries(params).forEach(([k, v]) => url.searchParams.set(k, v));
    }
    const res = await fetch(url.toString(), {
        headers: {"Content-Type": "application/json"},
    });
    return handleResponse<T>(res);
}

export async function apiPost<T>(path: string, body?: unknown): Promise<T> {
    const res = await fetch(`${BASE_URL}${path}`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: body ? JSON.stringify(body) : undefined,
    });
    return handleResponse<T>(res);
}

export async function apiPatch<T>(path: string, body?: unknown): Promise<T> {
    const res = await fetch(`${BASE_URL}${path}`, {
        method: "PATCH",
        headers: {"Content-Type": "application/json"},
        body: body ? JSON.stringify(body) : undefined,
    });
    return handleResponse<T>(res);
}

export async function apiPut<T>(path: string, body?: unknown): Promise<T> {
    const res = await fetch(`${BASE_URL}${path}`, {
        method: "PUT",
        headers: {"Content-Type": "application/json"},
        body: body ? JSON.stringify(body) : undefined,
    });
    return handleResponse<T>(res);
}

export function apiStream(path: string, body?: unknown): EventSource {
    // For SSE with POST, we need to use fetch with streaming
    // Return a custom EventSource-like object
    throw new Error("Use useSSE hook for streaming");
}

export async function apiPostStream(
    path: string,
    body: unknown,
    onChunk: (data: string) => void,
    onDone: () => void,
    onError: (err: Error) => void
): Promise<void> {
    try {
        const res = await fetch(`${BASE_URL}${path}`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Accept": "text/event-stream",
            },
            body: JSON.stringify(body),
        });

        if (!res.ok) {
            throw new ApiError(res.status, `HTTP ${res.status}`);
        }

        const reader = res.body?.getReader();
        if (!reader) throw new Error("No response body");

        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
            const {done, value} = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, {stream: true});
            const lines = buffer.split("\n");
            buffer = lines.pop() ?? "";

            for (const line of lines) {
                if (line.startsWith("data: ")) {
                    const data = line.slice(6).trim();
                    if (data === "[DONE]") {
                        onDone();
                        return;
                    }
                    onChunk(data);
                }
            }
        }
        onDone();
    } catch (err) {
        onError(err instanceof Error ? err : new Error(String(err)));
    }
}
