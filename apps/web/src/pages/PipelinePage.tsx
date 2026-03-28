export default function PipelinePage() {
  return (
    <div>
      <h1 style={{ marginTop: 0 }}>Pipeline Status</h1>
      <div className="empty-state">
        <p>No jobs running.</p>
        <p style={{ fontSize: "0.875rem" }}>Upload data to start a pipeline job.</p>
      </div>
    </div>
  );
}
