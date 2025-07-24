import api from './api';

class StockService {
  // Stock Levels API
  async getStockLevels(filters = {}) {
    const params = new URLSearchParams();
    
    if (filters.warehouseId) params.append('warehouse_id', filters.warehouseId);
    if (filters.variantId) params.append('variant_id', filters.variantId);
    if (filters.stockStatus) params.append('stock_status', filters.stockStatus);
    if (filters.minQuantity) params.append('min_quantity', filters.minQuantity);
    if (filters.includeZeroStock !== undefined) params.append('include_zero_stock', filters.includeZeroStock);
    if (filters.limit) params.append('limit', filters.limit);
    if (filters.offset) params.append('offset', filters.offset);

    const response = await api.get(`/stock-levels/?${params.toString()}`);
    return response.data;
  }

  async getAvailableStock(warehouseId, variantId, stockStatus = 'ON_HAND', requestedQuantity = null) {
    const params = new URLSearchParams();
    params.append('stock_status', stockStatus);
    if (requestedQuantity) params.append('requested_quantity', requestedQuantity);

    const response = await api.get(`/stock-levels/available/${warehouseId}/${variantId}?${params.toString()}`);
    return response.data;
  }

  async checkStockAvailability(warehouseId, variantId, requestedQuantity, stockStatus = 'ON_HAND') {
    const params = new URLSearchParams();
    params.append('requested_quantity', requestedQuantity);
    params.append('stock_status', stockStatus);

    const response = await api.get(`/stock-levels/availability-check/${warehouseId}/${variantId}?${params.toString()}`);
    return response.data;
  }

  async getStockSummary(warehouseId, variantId) {
    const response = await api.get(`/stock-levels/summary/${warehouseId}/${variantId}`);
    return response.data;
  }

  async getWarehouseStockSummaries(warehouseId, limit = 100, offset = 0) {
    const params = new URLSearchParams();
    params.append('limit', limit);
    params.append('offset', offset);

    const response = await api.get(`/stock-levels/summaries/${warehouseId}?${params.toString()}`);
    return response.data;
  }

  // Stock Operations
  async adjustStockLevel(adjustment) {
    const response = await api.post('/stock-levels/adjust', adjustment);
    return response.data;
  }

  async reserveStock(reservation) {
    const response = await api.post('/stock-levels/reserve', reservation);
    return response.data;
  }

  async releaseReservation(reservation) {
    const response = await api.post('/stock-levels/release-reservation', reservation);
    return response.data;
  }

  async transferBetweenWarehouses(transfer) {
    const response = await api.post('/stock-levels/transfer-warehouses', transfer);
    return response.data;
  }

  async transferBetweenStatuses(transfer) {
    const response = await api.post('/stock-levels/transfer-status', transfer);
    return response.data;
  }

  async reconcilePhysicalCount(reconciliation) {
    const response = await api.post('/stock-levels/reconcile-physical-count', reconciliation);
    return response.data;
  }

  // Stock Alerts
  async getLowStockAlerts(minimumThreshold = 10) {
    const params = new URLSearchParams();
    params.append('minimum_threshold', minimumThreshold);

    const response = await api.get(`/stock-levels/alerts/low-stock?${params.toString()}`);
    return response.data;
  }

  async getNegativeStockReport() {
    const response = await api.get('/stock-levels/alerts/negative-stock');
    return response.data;
  }

  // Stock Documents API  
  async getStockDocuments(filters = {}) {
    const params = new URLSearchParams();
    
    if (filters.docType) params.append('doc_type', filters.docType);
    if (filters.docStatus) params.append('doc_status', filters.docStatus);
    if (filters.warehouseId) params.append('warehouse_id', filters.warehouseId);
    if (filters.limit) params.append('limit', filters.limit);
    if (filters.offset) params.append('offset', filters.offset);

    const response = await api.get(`/stock-docs/?${params.toString()}`);
    return response.data;
  }

  async getStockDocumentsByRefAndStatus(refDocId = null, status = null) {
    const payload = {};
    if (refDocId) payload.ref_doc_id = refDocId;
    if (status) payload.status = status;

    const response = await api.post('/stock-docs/get', payload);
    return response.data;
  }

  async getStockDocument(docId) {
    const response = await api.get(`/stock-docs/${docId}`);
    return response.data;
  }

  async createStockDocument(stockDoc) {
    const response = await api.post('/stock-docs/', stockDoc);
    return response.data;
  }

  async updateStockDocument(docId, updates) {
    const response = await api.put(`/stock-docs/${docId}`, updates);
    return response.data;
  }

  async postStockDocument(docId) {
    const response = await api.post(`/stock-docs/${docId}/post`);
    return response.data;
  }

  async cancelStockDocument(docId, reason = '') {
    const response = await api.post(`/stock-docs/${docId}/cancel`, { reason });
    return response.data;
  }

  async getStockDocumentsByType(docType, limit = 100, offset = 0) {
    const params = new URLSearchParams();
    params.append('limit', limit);
    params.append('offset', offset);

    const response = await api.get(`/stock-docs/type/${docType}?${params.toString()}`);
    return response.data;
  }

  async getStockDocumentsByStatus(docStatus, limit = 100, offset = 0) {
    const params = new URLSearchParams();
    params.append('limit', limit);
    params.append('offset', offset);

    const response = await api.get(`/stock-docs/status/${docStatus}?${params.toString()}`);
    return response.data;
  }

  async getStockDocumentsByWarehouse(warehouseId, limit = 100, offset = 0) {
    const params = new URLSearchParams();
    params.append('limit', limit);
    params.append('offset', offset);

    const response = await api.get(`/stock-docs/warehouse/${warehouseId}?${params.toString()}`);
    return response.data;
  }

  async getPendingTransfers(warehouseId) {
    const response = await api.get(`/stock-docs/warehouse/${warehouseId}/pending-transfers`);
    return response.data;
  }

  // Specialized Stock Document Creation
  async createConversion(conversion) {
    const response = await api.post('/stock-docs/conversions', conversion);
    return response.data;
  }

  async createTransfer(transfer) {
    const response = await api.post('/stock-docs/transfers', transfer);
    return response.data;
  }

  async createTruckLoad(truckLoad) {
    const response = await api.post('/stock-docs/truck-loads', truckLoad);
    return response.data;
  }

  async createTruckUnload(truckUnload) {
    const response = await api.post('/stock-docs/truck-unloads', truckUnload);
    return response.data;
  }

  async generateDocumentNumber(docType) {
    const response = await api.get(`/stock-docs/generate-number/${docType}`);
    return response.data;
  }

  async getMovementsSummary(filters = {}) {
    const response = await api.post('/stock-docs/movements/summary', filters);
    return response.data;
  }
}

export default new StockService();