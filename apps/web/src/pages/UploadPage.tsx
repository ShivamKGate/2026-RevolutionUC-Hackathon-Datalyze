export default function UploadPage() {
  return (
    <div>
      <h1 style={{ marginTop: 0 }}>Upload Data</h1>
      <div className="dropzone">
        <p style={{ fontSize: "1.1rem", marginBottom: "0.5rem" }}>
          Drag &amp; drop files here, or click to browse
        </p>
        <p style={{ fontSize: "0.875rem" }}>
          Supported formats: CSV, Excel (.xlsx), JSON, PDF
        </p>
      </div>
    </div>
  );
}
