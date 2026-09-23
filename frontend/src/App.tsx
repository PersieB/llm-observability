import { useEffect, useState } from "react";
import {
  LineChart,
  Line,
  Bar,
  BarChart,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { getMetrics, getTraces, getTrace } from "./api";

function App() {
  const [metrics, setMetrics] = useState<any>(null);
  const [traces, setTraces] = useState<any[]>([]);
  const [statusFilter, setStatusFilter] = useState("all");
  const [selectedTraceId, setSelectedTraceId] = useState<string | null>(null);
  const [selectedTrace, setSelectedTrace] = useState<any>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
const loadDashboardData = async () => {
  setIsRefreshing(true);

  try {
    const [metricsData, tracesData] = await Promise.all([
      getMetrics(),
      getTraces(),
    ]);

    setMetrics(metricsData);
    setTraces(tracesData);
  } catch (error) {
    console.error(error);
  } finally {
    setIsRefreshing(false);
  }
};
  const latencyData = traces
    .filter(
      (trace) =>
        trace.status === "success" &&
        trace.retrieval_latency !== null &&
        trace.llm_latency !== null
    )
    .slice(0, 20)
    .reverse()
    .map((trace, index) => ({
      request: index + 1,
      retrieval: trace.retrieval_latency,
      llm: trace.llm_latency,
    }));
  const successCount = traces.filter(
  (trace) => trace.status === "success"
).length;

  const errorCount = traces.filter(
    (trace) => trace.status === "error"
  ).length;

  const totalTraceCount = successCount + errorCount;

  const successRate =
    totalTraceCount > 0
      ? (successCount / totalTraceCount) * 100
      : 0;
  const failureData = traces
  .filter((trace) => trace.status === "error")
  .reduce((acc: Record<string, number>, trace) => {
    const stage = trace.error_stage || "unknown";
    acc[stage] = (acc[stage] || 0) + 1;
    return acc;
  }, {});

  const failureStageData = Object.entries(failureData).map(
  ([stage, count]) => ({
    stage,
    count,
  })
);

  useEffect(() => {
    loadDashboardData();
  }, []);

  useEffect(() => {
  if (!selectedTraceId) {
    return;
  }

  getTrace(selectedTraceId)
    .then((data) => {
      setSelectedTrace(data);
    })
    .catch((error) => {
      console.error(error);
    });
}, [selectedTraceId]);
  const filteredTraces =
    statusFilter === "all"
      ? traces
      : traces.filter((trace) => trace.status === statusFilter);




  return (
    <div>
    <header className="dashboard-header">
      <div>
        <h1>RAG Observability Platform</h1>
        <p>Monitor performance, usage, and reliability of your LLM application.</p>
      </div>

      <button
        className="refresh-button"
        onClick={loadDashboardData}
        disabled={isRefreshing}
      >
        {isRefreshing ? "Refreshing..." : "Refresh Data"}
      </button>
    </header>

      <main>
        <section>
            <div className="section-header">
              <h2>Overview</h2>

              {isRefreshing && <span className="loading-text">Updating...</span>}
            </div>

          <div>
            <div>
              <h3>Total Requests</h3>
              <p>{metrics ? metrics.total_requests.toLocaleString() : "--"}</p>
            </div>

            <div>
              <h3>Average Latency</h3>
              <p>
              {metrics ? `${metrics.average_latency?.toFixed(2)}s` : "--"}
            </p>
            </div>

            <div>
              <h3>Error Rate</h3>
              <p>
              {metrics ? `${(metrics.error_rate * 100).toFixed(1)}%` : "--"}
            </p>
            </div>

            <div>
              <h3>Total Tokens</h3>
              <p>{metrics ? metrics.total_tokens.toLocaleString() : "--"}</p>
            </div>
            <div className="metric-card">
              <h3>Request Health</h3>

              <div className="health-rate">
                {successRate.toFixed(1)}%
              </div>

              <p>
                {successCount} successful · {errorCount} failed
              </p>

              <small>
                Based on the latest {totalTraceCount} traces
              </small>
            </div>
          </div>
        </section>

        <section>
          <h2>Latency by Recent Request</h2>
          <p>Comparison of retrieval and LLM latency across recent requests.</p>

          <div
            style={{
              background: "white",
              border: "1px solid #ddd",
              borderRadius: "8px",
              padding: "20px",
            }}
          >
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={latencyData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="request"
                  label={{
                    value: "Recent request",
                    position: "insideBottom",
                    offset: -5,
                  }}
                />
                <YAxis
                  label={{
                    value: "Latency (seconds)",
                    angle: -90,
                    position: "insideLeft",
                  }}
                />
                <Legend />
                <Tooltip />
                <Line
                  type="monotone"
                  dataKey="retrieval"
                  stroke="#8884d8"
                  name="Retrieval"
                />
                <Line
                  type="monotone"
                  dataKey="llm"
                  stroke="#82ca9d"
                  name="LLM"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </section>
        <section>
        <h2>Failure Analysis</h2>
        <p>Requests grouped by the stage where they failed.</p>

        {failureStageData.length > 0 ? (
          <div className="chart-card">
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={failureStageData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="stage" />
                <YAxis allowDecimals={false} />
                <Tooltip />
                <Bar dataKey="count" name="Failed Requests" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <p>No failed requests in the current trace window.</p>
        )}
</section>
    <section>
      <div className="traces-header">
        <h2>Recent Traces</h2>

        <div className="trace-filters">
          <button
            className={statusFilter === "all" ? "active" : ""}
            onClick={() => setStatusFilter("all")}
          >
            All
          </button>

          <button
            className={statusFilter === "success" ? "active" : ""}
            onClick={() => setStatusFilter("success")}
          >
            Success
          </button>

          <button
            className={statusFilter === "error" ? "active" : ""}
            onClick={() => setStatusFilter("error")}
          >
            Errors
          </button>
        </div>
      </div>

      <table>
        <thead>
          <tr>
            <th>Time</th>
            <th>Question</th>
            <th>Status</th>
            <th>Retrieval</th>
            <th>LLM</th>
            <th>Total</th>
            <th>Tokens</th>
          </tr>
        </thead>

        <tbody>
          {filteredTraces.map((trace) => (
            <tr
              key={trace.trace_id}
              onClick={() => setSelectedTraceId(trace.trace_id)}
            >
              <td>
                {trace.timestamp
                  ? new Date(trace.timestamp).toLocaleString()
                  : "--"}
              </td>

              <td>{trace.question}</td>

              <td>
                <span className={`status ${trace.status}`}>
                  {trace.status}
                </span>
              </td>

              <td>
                {trace.retrieval_latency !== null
                  ? `${trace.retrieval_latency.toFixed(2)}s`
                  : "--"}
              </td>

              <td>
                {trace.llm_latency !== null
                  ? `${trace.llm_latency.toFixed(2)}s`
                  : "--"}
              </td>

              <td>
                {trace.total_latency !== null
                  ? `${trace.total_latency.toFixed(2)}s`
                  : "--"}
              </td>

              <td>
                {trace.total_tokens !== null
                  ? trace.total_tokens.toLocaleString()
                  : "--"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
        {selectedTrace && (
          <div className="modal-overlay">
            <div className="trace-modal">
              <div className="modal-header">
                <h2>Trace Details</h2>

                <button
                  type="button"
                  onClick={() => {
                    setSelectedTrace(null);
                    setSelectedTraceId(null);
                  }}
                >
                  ×
                </button>
              </div>

              <div className="trace-details">
            <div>
              <h3>Question</h3>
              <p>{selectedTrace.question}</p>
            </div>

            <div>
              <h3>Answer</h3>
              <p>{selectedTrace.answer || "--"}</p>
            </div>
            <div>
              <h3>Status</h3>
              <span className={`status ${selectedTrace.status}`}>
                {selectedTrace.status}
              </span>
            </div>

            <div className="detail-grid">
              <div>
                <h3>Performance</h3>

                <p>
                  Embedding:{" "}
                  {selectedTrace.embedding_latency !== null
                    ? `${selectedTrace.embedding_latency.toFixed(2)}s`
                    : "--"}
                </p>

                <p>
                  Vector Search:{" "}
                  {selectedTrace.vector_search_latency !== null
                    ? `${selectedTrace.vector_search_latency.toFixed(2)}s`
                    : "--"}
                </p>

                <p>
                  Retrieval:{" "}
                  {selectedTrace.retrieval_latency !== null
                    ? `${selectedTrace.retrieval_latency.toFixed(2)}s`
                    : "--"}
                </p>

                <p>
                  LLM:{" "}
                  {selectedTrace.llm_latency !== null
                    ? `${selectedTrace.llm_latency.toFixed(2)}s`
                    : "--"}
                </p>

                <p>
                  Total:{" "}
                  {selectedTrace.total_latency !== null
                    ? `${selectedTrace.total_latency.toFixed(2)}s`
                    : "--"}
                </p>
              </div>

              <div>
                <h3>Token Usage</h3>

                <p>
                  Input:{" "}
                  {selectedTrace.input_tokens !== null
                    ? selectedTrace.input_tokens.toLocaleString()
                    : "--"}
                </p>

                <p>
                  Output:{" "}
                  {selectedTrace.output_tokens !== null
                    ? selectedTrace.output_tokens.toLocaleString()
                    : "--"}
                </p>

                <p>
                  Thoughts:{" "}
                  {selectedTrace.thought_tokens !== null
                    ? selectedTrace.thought_tokens.toLocaleString()
                    : "--"}
                </p>

                <p>
                  Total:{" "}
                  {selectedTrace.total_tokens !== null
                    ? selectedTrace.total_tokens.toLocaleString()
                    : "--"}
                </p>
              </div>
            </div>
            </div>
          </div>
        </div>
      )}
      </main>
    </div>
  );
}

export default App;