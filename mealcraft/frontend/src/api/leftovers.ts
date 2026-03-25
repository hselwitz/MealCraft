import {apiGet, apiPatch, apiPost} from "./client";
import type {CreateLeftoverRequest, Leftover} from "@/types";

export const leftoversApi = {
    list: (status?: string) =>
        apiGet<Leftover[]>("/leftovers", status ? {status} : undefined),

    create: (body: CreateLeftoverRequest) => apiPost<Leftover>("/leftovers", body),

    update: (id: string, body: { status?: string; remaining_servings?: number; used_in_slot_id?: string }) =>
        apiPatch<Leftover>(`/leftovers/${id}`, body),

    getSuggestions: (emptySlots?: string[]) =>
        apiPost<{ suggestions: string[] }>("/leftovers/suggestions", {
            empty_slots: emptySlots ?? [],
        }),
};
