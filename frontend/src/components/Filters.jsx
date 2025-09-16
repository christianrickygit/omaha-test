import { useState, useEffect } from 'react';
import { getLocations, getMetrics } from '../api';

const QUALITY_OPTIONS = [
  { value: '', label: 'Any' },
  { value: 'excellent', label: 'Excellent' },
  { value: 'good', label: 'Good' },
  { value: 'poor', label: 'Poor' },
];

const ANALYSIS_TYPES = [
  { value: 'raw', label: 'Climate Data' },
  { value: 'weighted', label: 'Summary' },
  { value: 'trends', label: 'Trends' },
];

function Filters({ filters, onFilterChange, onApplyFilters }) {
  const [localFilters, setLocalFilters] = useState({
    locationId: filters.locationId || '',
    startDate: filters.startDate || '',
    endDate: filters.endDate || '',
    metric: filters.metric || '',
    qualityThreshold: filters.qualityThreshold || '',
    analysisType: filters.analysisType || 'raw'
  });
  const [locations, setLocations] = useState([]);
  const [metrics, setMetrics] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchDropdowns() {
      setLoading(true);
      try {
        const [locRes, metRes] = await Promise.all([getLocations(), getMetrics()]);
        setLocations(locRes.data || []);
        setMetrics(metRes.data || []);
      } catch (err) {
        setLocations([]);
        setMetrics([]);
      }
      setLoading(false);
    }
    fetchDropdowns();
  }, []);

  // Sync with parent filters if they change
  useEffect(() => {
    setLocalFilters({
      locationId: filters.locationId || '',
      startDate: filters.startDate || '',
      endDate: filters.endDate || '',
      metric: filters.metric || '',
      qualityThreshold: filters.qualityThreshold || '',
      analysisType: filters.analysisType || 'raw'
    });
  }, [filters]);

  const handleChange = (field, value) => {
    const updated = { ...localFilters, [field]: value };
    setLocalFilters(updated);
  };

  const handleApply = (e) => {
    e.preventDefault();
    if (onApplyFilters) {
      onApplyFilters(localFilters);
    }
  };

  const handleClear = () => {
    const cleared = {
      locationId: '',
      startDate: '',
      endDate: '',
      metric: '',
      qualityThreshold: '',
      analysisType: 'raw'
    };
    setLocalFilters(cleared);
    if (onApplyFilters) {
      onApplyFilters(cleared);
    }
  };

  return (
    <form
      className="bg-white p-4 rounded-lg shadow-md grid grid-cols-1 md:grid-cols-2 gap-4"
      onSubmit={handleApply}
    >
      <div>
        <label className="block text-sm font-medium mb-1">Location</label>
        <select
          className="w-full border rounded px-2 py-1"
          value={localFilters.locationId}
          onChange={e => handleChange('locationId', e.target.value)}
          disabled={loading}
        >
          <option value="">Select location</option>
          {locations.map(loc => (
            <option key={loc.id} value={loc.id}>
              {loc.name} {loc.region ? `(${loc.region})` : ''}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium mb-1">Metric</label>
        <select
          className="w-full border rounded px-2 py-1"
          value={localFilters.metric}
          onChange={e => handleChange('metric', e.target.value)}
          disabled={loading}
        >
          <option value="">Any metric</option>
          {metrics.map(m => (
            <option key={m.id} value={m.name}>
              {m.display_name || m.name}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium mb-1">Start Date</label>
        <input
          type="date"
          className="w-full border rounded px-2 py-1"
          value={localFilters.startDate}
          onChange={e => handleChange('startDate', e.target.value)}
        />
      </div>

      <div>
        <label className="block text-sm font-medium mb-1">End Date</label>
        <input
          type="date"
          className="w-full border rounded px-2 py-1"
          value={localFilters.endDate}
          onChange={e => handleChange('endDate', e.target.value)}
        />
      </div>

      <div>
        <label className="block text-sm font-medium mb-1">Quality Threshold</label>
        <select
          className="w-full border rounded px-2 py-1"
          value={localFilters.qualityThreshold}
          onChange={e => handleChange('qualityThreshold', e.target.value)}
        >
          {QUALITY_OPTIONS.map(opt => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium mb-1">Analysis Type</label>
        <select
          className="w-full border rounded px-2 py-1"
          value={localFilters.analysisType}
          onChange={e => handleChange('analysisType', e.target.value)}
        >
          {ANALYSIS_TYPES.map(opt => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
        </select>
      </div>

      <div className="md:col-span-2 flex justify-end mt-2 space-x-2">
        <button
          type="button"
          className="bg-gray-200 text-gray-700 px-4 py-2 rounded hover:bg-gray-300 transition"
          onClick={handleClear}
          disabled={loading}
        >
          Clear Filters
        </button>
        <button
          type="submit"
          className="bg-eco-primary text-white px-4 py-2 rounded hover:bg-eco-primary-dark transition"
          disabled={loading}
        >
          {loading ? "Loading..." : "Apply Filters"}
        </button>
      </div>
    </form>
  );
}

export default Filters;