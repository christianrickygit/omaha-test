import { Bar } from 'react-chartjs-2';
import { Chart, BarElement, CategoryScale, LinearScale, Tooltip, Legend } from 'chart.js';
Chart.register(BarElement, CategoryScale, LinearScale, Tooltip, Legend);

function SummaryTable({ data, loading }) {
  if (loading) return <div className="text-center py-8 text-lg">Loading summary...</div>;
  if (!data || Object.keys(data).length === 0) return <div className="text-center py-8 text-gray-500">No summary data.</div>;

  // Prepare chart data for each metric with quality_distribution
  const metricsWithQuality = Object.entries(data).filter(
    ([, stats]) => stats.quality_distribution
  );

  // Helper to round to 2 decimals
  const round2 = (v) => v === null || v === undefined ? '-' : Number(v).toFixed(2);

  return (
    <div className="space-y-8 w-full col-span-2">
      <div className="overflow-x-auto rounded shadow border bg-white w-full">
        <table className="min-w-full text-sm">
          <thead className="bg-eco-primary text-white">
            <tr>
              <th className="px-4 py-2 border">Metric</th>
              <th className="px-4 py-2 border">Min</th>
              <th className="px-4 py-2 border">Max</th>
              <th className="px-4 py-2 border">Avg</th>
              <th className="px-4 py-2 border">Weighted Avg</th>
              <th className="px-4 py-2 border">Unit</th>
              <th className="px-4 py-2 border">Quality Distribution</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(data).map(([metric, stats], idx) => (
              <tr key={metric} className={idx % 2 === 0 ? "bg-gray-50" : ""}>
                <td className="px-4 py-2 border font-semibold">{metric}</td>
                <td className="px-4 py-2 border">{round2(stats.min)}</td>
                <td className="px-4 py-2 border">{round2(stats.max)}</td>
                <td className="px-4 py-2 border">{round2(stats.avg)}</td>
                <td className="px-4 py-2 border">{round2(stats.weighted_avg)}</td>
                <td className="px-4 py-2 border">{stats.unit ?? '-'}</td>
                <td className="px-4 py-2 border">
                  {stats.quality_distribution
                    ? Object.entries(stats.quality_distribution)
                        .map(([q, v]) => (
                          <span
                            key={q}
                            className={`inline-block px-2 py-1 mr-1 rounded text-xs font-medium ${
                              q === "excellent"
                                ? "bg-green-100 text-green-700"
                                : q === "good"
                                ? "bg-blue-100 text-blue-700"
                                : q === "questionable"
                                ? "bg-yellow-100 text-yellow-700"
                                : "bg-red-100 text-red-700"
                            }`}
                          >
                            {q}: {(v * 100).toFixed(2)}%
                          </span>
                        ))
                    : "-"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Show a bar chart for quality distribution if available */}
      {metricsWithQuality.length > 0 && (
        <div className="bg-white rounded shadow p-4 w-full">
          <h3 className="text-lg font-semibold mb-4">Quality Distribution by Metric</h3>
          <Bar
            data={{
              labels: metricsWithQuality.map(([metric]) => metric),
              datasets: [
                {
                  label: "Excellent",
                  backgroundColor: "#22c55e",
                  data: metricsWithQuality.map(
                    ([, stats]) => Number((stats.quality_distribution?.excellent ?? 0).toFixed(2))
                  ),
                },
                {
                  label: "Good",
                  backgroundColor: "#3b82f6",
                  data: metricsWithQuality.map(
                    ([, stats]) => Number((stats.quality_distribution?.good ?? 0).toFixed(2))
                  ),
                },
                {
                  label: "Questionable",
                  backgroundColor: "#facc15",
                  data: metricsWithQuality.map(
                    ([, stats]) => Number((stats.quality_distribution?.questionable ?? 0).toFixed(2))
                  ),
                },
                {
                  label: "Poor",
                  backgroundColor: "#ef4444",
                  data: metricsWithQuality.map(
                    ([, stats]) => Number((stats.quality_distribution?.poor ?? 0).toFixed(2))
                  ),
                },
              ],
            }}
            options={{
              responsive: true,
              plugins: {
                legend: { position: "top" },
                tooltip: {
                  callbacks: {
                    label: function (context) {
                      return `${context.dataset.label}: ${(context.parsed.y * 100).toFixed(2)}%`;
                    },
                  },
                },
              },
              scales: {
                y: {
                  beginAtZero: true,
                  max: 1,
                  ticks: {
                    callback: (v) => `${(v * 100).toFixed(0)}%`,
                  },
                  title: { display: true, text: "Percentage" },
                },
              },
            }}
            height={300}
          />
        </div>
      )}
    </div>
  );
}

export default SummaryTable;