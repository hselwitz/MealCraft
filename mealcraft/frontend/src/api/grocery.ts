import {apiGet, apiPatch} from "./client";
import type {GroceryItem, GroceryList} from "@/types";

export const groceryApi = {
    get: (id: string) => apiGet<GroceryList>(`/grocery-lists/${id}`),

    updateItem: (listId: string, itemId: string, body: { checked?: boolean; quantity?: number; unit?: string }) =>
        apiPatch<GroceryItem>(`/grocery-lists/${listId}/items/${itemId}`, body),
};
