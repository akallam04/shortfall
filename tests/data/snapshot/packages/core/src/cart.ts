export function reserveInventory(items) {
  return items.map((item) => item.quantity)
}

export const LOCK_KEY = "cart"
