// src/components/TrendAnalysis.jsx
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

function TrendAnalysis({ data, loading }) {

  if (loading) {
    return (
      <div className="bg-white p-4 rounded-lg shadow-md animate-pulse col-span-2 w-full">
        <div className="h-64 bg-gray-200 rounded" />
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className="space-y-6 w-full col-span-2">
      {/* Trend Overview */}
      <div className="bg-white p-4 rounded-lg shadow-md w-full">
        <h3 className="text-lg font-semibold mb-4">Trend Analysis</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {Object.entries(data).map(([metric, analysis]) => (
            <div key={metric} className="p-4 border rounded-lg">
              <h4 className="font-medium text-gray-700 mb-2 capitalize">{metric}</h4>
              <div className="space-y-2">
                <TrendStat 
                  label="Trend Direction"
                  value={analysis.trend.direction ? analysis.trend.direction : "N/A"}
                  icon={getTrendIcon(analysis.trend.direction)}
                />
                <TrendStat 
                  label="Rate of Change"
                  value={
                    analysis.trend.rate !== null && analysis.trend.unit
                      ? `${Number(analysis.trend.rate).toFixed(2)} ${analysis.trend.unit}/month`
                      : "N/A"
                  }
                />
                <TrendStat 
                  label="Confidence"
                  value={
                    analysis.trend.confidence !== null
                      ? `${(analysis.trend.confidence * 100).toFixed(1)}%`
                      : "N/A"
                  }
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Anomalies */}
      <div className="bg-white p-4 rounded-lg shadow-md w-full">
        <h3 className="text-lg font-semibold mb-4">Detected Anomalies</h3>
        <div className="space-y-2">
          {Object.entries(data).map(([metric, analysis]) => (
            analysis.anomalies.length > 0 && (
              <div key={metric} className="border-b pb-2">
                <h4 className="font-medium text-gray-700 mb-2 capitalize">{metric}</h4>
                <div className="space-y-1">
                  {analysis.anomalies.map((anomaly, index) => (
                    <div key={index} className="flex items-center text-sm">
                      <span className="w-32">{anomaly.date}</span>
                      <span className="w-24">{Number(anomaly.value).toFixed(2)}</span>
                      <span className={`px-2 py-1 rounded text-xs ${
                        anomaly.deviation > 3 ? 'bg-red-100 text-red-800' : 'bg-yellow-100 text-yellow-800'
                      }`}>
                        {Number(anomaly.deviation).toFixed(2)} σ
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )
          ))}
        </div>
      </div>

      {/* Seasonality */}
      <div className="bg-white p-4 rounded-lg shadow-md w-full">
        <h3 className="text-lg font-semibold mb-4">Seasonal Patterns</h3>
        <div className="space-y-4">
          {Object.entries(data).map(([metric, analysis]) => (
            analysis.seasonality.detected && (
              <div key={metric} className="border-b pb-4">
                <h4 className="font-medium text-gray-700 mb-2 capitalize">{metric}</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-gray-600">
                      Period: {analysis.seasonality.period ? analysis.seasonality.period : "N/A"}
                    </p>
                    <p className="text-sm text-gray-600">
                      Confidence: {analysis.seasonality.confidence !== null
                        ? (analysis.seasonality.confidence * 100).toFixed(1) + '%'
                        : 'N/A'}
                    </p>
                  </div>
                  <div className="space-y-1">
                    {Object.entries(analysis.seasonality.pattern).map(([season, data]) => (
                      <div key={season} className="flex justify-between text-sm">
                        <span className="capitalize">{season}</span>
                        <span>
                          {data.avg !== null && data.avg !== undefined
                            ? Number(data.avg).toFixed(2)
                            : 'N/A'} ({data.trend ? data.trend : "N/A"})
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )
          ))}
        </div>
      </div>
    </div>
  );
}

function TrendStat({ label, value, icon }) {
  return (
    <div className="flex justify-between items-center text-sm">
      <span className="text-gray-600">{label}:</span>
      <span className="font-medium flex items-center gap-1">
        {icon && <span>{icon}</span>}
        {value}
      </span>
    </div>
  );
}

function getTrendIcon(direction) {
  if (!direction || typeof direction !== "string") return null;
  switch (direction.toLowerCase()) {
    case 'increasing':
      return '↗️';
    case 'decreasing':
      return '↘️';
    case 'stable':
      return '➡️';
    default:
      return null;
  }
}

export default TrendAnalysis;