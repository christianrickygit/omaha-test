import { useState, useEffect } from 'react';
import Filters from './components/Filters';
import ChartContainer from './components/ChartContainer';
import TrendAnalysis from './components/TrendAnalysis';
import QualityIndicator from './components/QualityIndicator';
import SummaryTable from './components/SummaryTable';

function App() {
  const [locations, setLocations] = useState([]);
  const [metrics, setMetrics] = useState([]);
  const [climateData, setClimateData] = useState([]);
  const [trendData, setTrendData] = useState(null);
  const [summaryData, setSummaryData] = useState(null);
  const [filters, setFilters] = useState({
    locationId: '',
    startDate: '',
    endDate: '',
    metric: '',
    qualityThreshold: '',
    analysisType: 'raw'
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchData = async (appliedFilters) => {
    setLoading(true);
    setError(null);
    try {
      const queryParams = new URLSearchParams({
        ...(appliedFilters.locationId && { location_id: appliedFilters.locationId }),
        ...(appliedFilters.startDate && { start_date: appliedFilters.startDate }),
        ...(appliedFilters.endDate && { end_date: appliedFilters.endDate }),
        ...(appliedFilters.metric && { metric: appliedFilters.metric }),
        ...(appliedFilters.qualityThreshold && { quality_threshold: appliedFilters.qualityThreshold })
      });

      let endpoint = '/api/v1/climate';
      if (appliedFilters.analysisType === 'trends') {
        endpoint = '/api/v1/trends';
      } else if (appliedFilters.analysisType === 'weighted') {
        endpoint = '/api/v1/summary';
      }

      const response = await fetch(`${endpoint}?${queryParams}`);
      if (!response.ok) {
        throw new Error(`API error: ${response.status} ${response.statusText}`);
      }
      const data = await response.json();

      // Handle empty or missing data 
      if (!data || !data.data || (Array.isArray(data.data) && data.data.length === 0) || (typeof data.data === 'object' && Object.keys(data.data).length === 0)) {
        setError("No data available for the selected filters.");
        setTrendData(null);
        setSummaryData(null);
        setClimateData([]);
        setLoading(false);
        return;
      }

      if (appliedFilters.analysisType === 'trends') {
        setTrendData(data.data);
        setSummaryData(null);
        setClimateData([]);
      } else if (appliedFilters.analysisType === 'weighted') {
        setSummaryData(data.data);
        setTrendData(null);
        setClimateData([]);
      } else {
        setClimateData(data.data);
        setTrendData(null);
        setSummaryData(null);
      }
    } catch (error) {
      setError(error.message || 'Error fetching data.');
      setTrendData(null);
      setSummaryData(null);
      setClimateData([]);
    } finally {
      setLoading(false);
    }
  };

  const handleApplyFilters = (newFilters) => {
    setFilters(newFilters);
    fetchData(newFilters);
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-6xl">
      <header className="mb-8 text-center">
        <h1 className="text-4xl font-bold text-eco-primary mb-2">
          EcoVision: Climate Visualizer
        </h1>
        <p className="text-gray-600 italic">
          Transforming climate data into actionable insights for a sustainable future
        </p>
      </header>

      <Filters 
        locations={locations}
        metrics={metrics}
        filters={filters}
        onFilterChange={setFilters}
        onApplyFilters={handleApplyFilters}
      />

      {error && (
        <div className="bg-red-100 text-red-700 px-4 py-3 rounded mb-6 text-center">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-8">
        {filters.analysisType === 'trends' ? (
          <TrendAnalysis 
            data={trendData}
            loading={loading}
          />
        ) : filters.analysisType === 'weighted' ? (
          <SummaryTable
            data={summaryData}
            loading={loading}
          />
        ) : (
          <>
            <ChartContainer 
              title="Climate Trends"
              loading={loading}
              chartType="line"
              data={climateData}
              showQuality={true}
            />
            <ChartContainer 
              title="Quality Distribution"
              loading={loading}
              chartType="bar"
              data={climateData}
              showQuality={true}
            />
          </>
        )}
      </div>

      <QualityIndicator 
        data={climateData}
        className="mt-6"
      />
    </div>
  );
}

export default App;