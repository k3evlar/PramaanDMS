import { useEffect, useState } from "react";
import { fetchServiceStatus, type ServiceStatus } from "./api";

// Phase 3 placeholder page. Real screens (upload, verify, change view) arrive in Phase 9.
// All text is rendered by React as text, never as raw HTML.

const STATUS_TEXT: Record<ServiceStatus, string> = {
  checking: "Checking the service...",
  available: "The service is running.",
  unavailable: "The service is not reachable. Please try again later.",
};

export default function App({ fetchImpl }: { fetchImpl?: typeof fetch }) {
  const [status, setStatus] = useState<ServiceStatus>("checking");

  useEffect(() => {
    let active = true;
    fetchServiceStatus(fetchImpl).then((s) => {
      if (active) setStatus(s);
    });
    return () => {
      active = false;
    };
  }, [fetchImpl]);

  return (
    <main className="page">
      <h1>Pramaan DMS</h1>
      <p className="lead">Secure document management with tamper-evident verification for FIRs, statements and charge sheets.</p>
      <p role="status" className={`status status-${status}`}>
        {STATUS_TEXT[status]}
      </p>
      <p className="note">Demo system. English documents only. All data is synthetic.</p>
    </main>
  );
}
