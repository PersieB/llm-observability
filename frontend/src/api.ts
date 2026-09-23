const API_URL = import.meta.env.VITE_API_URL;


export async function getMetrics() {
  const response = await fetch(`${API_URL}/metrics`);

  if (!response.ok) {
    throw new Error("Failed to fetch metrics");
  }

  return response.json();
}

export async function getTraces() {
  const response = await fetch(`${API_URL}/traces`);

  if (!response.ok) {
    throw new Error("Failed to fetch traces");
  }

  return response.json();
}

export async function getTrace(traceId: string) {
  const response = await fetch(`${API_URL}/traces/${traceId}`);

  if (!response.ok) {
    throw new Error("Failed to fetch trace");
  }

  return response.json();
}