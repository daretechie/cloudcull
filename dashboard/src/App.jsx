import React, { useEffect, useState } from 'react';
import './App.css';

function App() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Dynamically handle GitHub Pages base path
    const basePath = import.meta.env.BASE_URL.replace(/\/$/, "");
    fetch(`${basePath}/report.json`)
      .then(res => res.json())
      .then(json => {
        setData(json);
        setLoading(false);
      })
      .catch(err => {
        console.error("Failed to load report:", err);
        setLoading(false);
      });
  }, []);

  if (loading) return <div className="dashboard">Loading Audit Intelligence...</div>;
  if (!data) return <div className="dashboard">No Audit Report Found. Run a scan to generate data.</div>;

  return (
    <div className="dashboard">
      <header>
        <div className="logo">CLOUDCULL // SNIPER</div>
        <div className="badge badge-safe">GOVERNANCE ACTIVE</div>
      </header>

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-label">Total Monthly Waste</div>
          <div className="stat-value savings-highlight">
            ${data.summary.total_monthly_savings.toLocaleString(undefined, { minimumFractionDigits: 2 })}
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Zombie Nodes Detected</div>
          <div className="stat-value" style={{ color: 'var(--zombie)' }}>
            {data.summary.zombie_count}
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Last Audit Execution</div>
          <div className="stat-value" style={{ fontSize: '1rem' }}>
            {new Date(data.summary.timestamp).toLocaleString()}
          </div>
        </div>
      </div>

      <h2>Detailed Target List</h2>
      <table className="instance-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Type</th>
            <th>Owner</th>
            <th>Waste ($)</th>
            <th>Decision</th>
          </tr>
        </thead>
        <tbody>
          {data.instances.map(inst => (
            <tr key={inst.id}>
              <td style={{ fontFamily: 'monospace' }}>{inst.id}</td>
              <td>{inst.type}</td>
              <td>@{inst.owner}</td>
              <td>${(inst.rate * 24 * 30).toLocaleString()} /mo</td>
              <td>
                <span className={`badge ${inst.status === 'ZOMBIE' ? 'badge-zombie' : 'badge-safe'}`}>
                  {inst.status === 'ZOMBIE' ? '🎯 TERMINATE' : '✅ DEVELOPER'}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default App;
