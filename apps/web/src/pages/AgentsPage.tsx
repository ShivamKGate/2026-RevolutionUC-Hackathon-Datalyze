export default function AgentsPage() {
  return (
    <div>
      <h1 style={{ marginTop: 0 }}>Agent Activity</h1>
      <div className="empty-state">
        <p>No agent runs yet.</p>
        <p style={{ fontSize: "0.875rem" }}>Agent activity will appear here once a pipeline is running.</p>
      </div>
    </div>
  );
}
