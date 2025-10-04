// Simple event system for real-time data synchronization between components
class DataSyncService {
  constructor() {
    this.listeners = new Map();
  }

  // Subscribe to data change events
  subscribe(eventType, callback) {
    if (!this.listeners.has(eventType)) {
      this.listeners.set(eventType, new Set());
    }
    this.listeners.get(eventType).add(callback);

    // Return unsubscribe function
    return () => {
      const callbacks = this.listeners.get(eventType);
      if (callbacks) {
        callbacks.delete(callback);
      }
    };
  }

  // Emit data change events
  emit(eventType, data) {
    const callbacks = this.listeners.get(eventType);
    if (callbacks) {
      callbacks.forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error('Error in data sync callback:', error);
        }
      });
    }
  }

  // Clear all listeners (for cleanup)
  clear() {
    this.listeners.clear();
  }
}

// Create singleton instance
const dataSyncService = new DataSyncService();

// Event types
export const DATA_EVENTS = {
  ABSENCE_DATA_CHANGED: 'absence_data_changed',
  ABSENCE_DATA_SAVED: 'absence_data_saved',
  EMPLOYEE_DATA_CHANGED: 'employee_data_changed'
};

export default dataSyncService;