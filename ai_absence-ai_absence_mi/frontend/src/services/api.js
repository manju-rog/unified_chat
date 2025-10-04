const API_BASE_URL = 'http://localhost:8080/api';
const DEFAULT_HEADERS = {
  'Content-Type': 'application/json',
  'Accept': 'application/json',
};

const apiRequest = async (endpoint, options = {}) => {
  const url = `${API_BASE_URL}${endpoint}`;
  const config = {
    headers: DEFAULT_HEADERS,
    ...options,
  };
  if (config.body && typeof config.body === 'object') {
    config.body = JSON.stringify(config.body);
  }
  try {
    const response = await fetch(url, config);
    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`HTTP ${response.status}: ${errorText || response.statusText}`);
    }
    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      return await response.json();
    }
    return await response.text();
  } catch (error) {
    console.error(`API Error: ${config.method || 'GET'} ${url}`, error);
    throw error;
  }
};

export const employeeAPI = {
  getAll: () => apiRequest('/employees'),
  getById: (id) => apiRequest(`/employees/${id}`),
  create: (employeeData) => apiRequest('/employees', {
    method: 'POST',
    body: employeeData,
  }),
  update: (id, employeeData) => apiRequest(`/employees/${id}`, {
    method: 'PUT',
    body: employeeData,
  }),
  delete: (id) => apiRequest(`/employees/${id}`, {
    method: 'DELETE',
  }),
  getCount: () => apiRequest('/employees/count'),
  initialize: () => apiRequest('/employees/initialize', {
    method: 'POST',
  }),
};

export const absenceAPI = {
  getAll: () => apiRequest('/absences'),
  getById: (id) => apiRequest(`/absences/${id}`),
  create: (absenceData) => apiRequest('/absences', {
    method: 'POST',
    body: absenceData,
  }),
  update: (id, absenceData) => apiRequest(`/absences/${id}`, {
    method: 'PUT',
    body: absenceData,
  }),
  delete: (id) => apiRequest(`/absences/${id}`, {
    method: 'DELETE',
  }),
  bulkUpdate: (changes) => apiRequest('/absences/bulk-update', {
    method: 'PUT',
    body: { changes },
  }),
};

// Calendar API
export const calendarAPI = {
  getSummary: async ({ from, to, department }) =>
    apiRequest(`/absences/calendar?from=${from}&to=${to}${department ? `&department=${encodeURIComponent(department)}` : ''}`),
  getDayDetails: async ({ date, department, country = 'IN' }) =>
    apiRequest(`/absences/calendar/day-details?date=${date}${department ? `&department=${encodeURIComponent(department)}` : ''}&country=${country}`)
};

// Holidays API
export const holidaysAPI = {
  get: async ({ year, country = 'IN' }) =>
    apiRequest(`/holidays?year=${year}&country=${country}`)
};

export const apiUtils = {
  handleError: (error) => {
    console.error('API Error:', error);
    if (error.message.includes('404')) {
      return 'Record not found';
    } else if (error.message.includes('409')) {
      return 'Conflict: Record already exists or validation failed';
    } else if (error.message.includes('400')) {
      return 'Invalid data provided';
    } else if (error.message.includes('500')) {
      return 'Server error. Please try again later';
    } else if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
      return 'Cannot connect to server. Please check if backend is running on http://localhost:8080';
    } else {
      return error.message || 'An unexpected error occurred';
    }
  },
  checkServerStatus: async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/employees/count`, {
        method: 'GET',
        headers: DEFAULT_HEADERS,
        timeout: 5000
      });
      return response.ok;
    } catch (error) {
      console.warn('Backend server is not running:', error);
      return false;
    }
  },
};

export default {
  employees: employeeAPI,
  absences: absenceAPI,
  calendar: calendarAPI,
  holidays: holidaysAPI,
  utils: apiUtils,
};