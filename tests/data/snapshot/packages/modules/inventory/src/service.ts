export class InventoryService {
  reserve(quantity) {
    return reserveInventory([{ quantity }])
  }
}
