/**
 * API service module for making requests to the backend
 */

const API_BASE_URL = "/api/v1";

/**
 * Helper to build query string from filters object
 */
const buildQueryString = (params = {}) =>
  Object.entries(params)
    .filter(([_, v]) => v !== undefined && v !== null && v !== "")
    .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v)}`)
    .join("&");

/**
 * Fetch climate data with optional filters
 * @param {Object} filters - Filter parameters
 * @returns {Promise} - API response
 */
export const getClimateData = async (filters = {}) => {
  try {
    const query = buildQueryString(filters);
    const res = await fetch(
      `${API_BASE_URL}/climate${query ? `?${query}` : ""}`
    );
    if (!res.ok) throw new Error(await res.text());
    return await res.json();
  } catch (error) {
    console.error("API Error:", error);
    throw error;
  }
};

/**
 * Fetch all available locations
 * @returns {Promise} - API response
 */
export const getLocations = async () => {
  try {
    const res = await fetch(`${API_BASE_URL}/locations`);
    if (!res.ok) throw new Error(await res.text());
    return await res.json();
  } catch (error) {
    console.error("API Error:", error);
    throw error;
  }
};

/**
 * Fetch all available metrics
 * @returns {Promise} - API response
 */
export const getMetrics = async () => {
  try {
    const res = await fetch(`${API_BASE_URL}/metrics`);
    if (!res.ok) throw new Error(await res.text());
    return await res.json();
  } catch (error) {
    console.error("API Error:", error);
    throw error;
  }
};

/**
 * Fetch climate summary statistics with optional filters
 * @param {Object} filters - Filter parameters
 * @returns {Promise} - API response
 */
export const getClimateSummary = async (filters = {}) => {
  try {
    const query = buildQueryString(filters);
    const res = await fetch(
      `${API_BASE_URL}/summary${query ? `?${query}` : ""}`
    );
    if (!res.ok) throw new Error(await res.text());
    return await res.json();
  } catch (error) {
    console.error("API Error:", error);
    throw error;
  }
};

/**
 * Fetch climate trends with optional filters
 * @param {Object} filters - Filter parameters
 * @returns {Promise} - API response
 */
export const getClimateTrends = async (filters = {}) => {
  try {
    const query = buildQueryString(filters);
    const res = await fetch(
      `${API_BASE_URL}/trends${query ? `?${query}` : ""}`
    );
    if (!res.ok) throw new Error(await res.text());
    return await res.json();
  } catch (error) {
    console.error("API Error:", error);
    throw error;
  }
};
