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

  const basePath = import.meta.env.BASE_URL.replace(/\/$/, "");

  if (loading) return <div className="loading-screen">INITIALIZING CLOUDCULL PROTOCOL...</div>;
  if (!data) return <div className="error-screen">NO AUDIT DATA DETECTED. EXECUTE SCAN.</div>;

  return (
    <div className="app-container">
      <div className="glass-panel main-dashboard">
        <header className="dashboard-header">
          <img src={`${basePath}/logo.png`} alt="CloudCull Logo" className="brand-logo" />
          <div className="header-status">
            <span className="status-dot"></span> SYSTEM ONLINE
          </div>
        </header>

        <section className="hero-stats">
          <div className="hero-card savings-card">
            <div className="hero-label">POTENTIAL MONTHLY RECOVERY</div>
            <div className="hero-value glowing-text">
              ${data.summary.total_monthly_savings.toLocaleString(undefined, { minimumFractionDigits: 2 })}
            </div>
          </div>
        </section>

        <div className="secondary-stats">
          <div className="stat-item">
            <span className="stat-label">ZOMBIE NODES</span>
            <span className="stat-value text-zombie">{data.summary.zombie_count}</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">CLOUDS SCANNED</span>
            <span className="stat-value">3</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">LAST SCAN</span>
            <span className="stat-value">{new Date(data.summary.timestamp).toLocaleTimeString()}</span>
          </div>
        </div>

        <section className="targets-section">
          <h3>DETECTED ANOMALIES</h3>
          <div className="table-container">
            <table className="glass-table">
              <thead>
                <tr>
                  <th>INFRASTRUCTURE ID</th>
                  <th>TYPE</th>
                  <th>OWNER</th>
                  <th>WASTE / MO</th>
                  <th>ACTION</th>
                </tr>
              </thead>
              <tbody>
                {data.instances.map(inst => (
                  <tr key={inst.id}>
                    <td className="mono-font">{inst.id}</td>
                    <td>{inst.type}</td>
                    <td>@{inst.owner}</td>
                    <td className="text-white">${(inst.rate * 24 * 30).toLocaleString()}</td>
                    <td>
                      <span className={`status-badge ${inst.status === 'ZOMBIE' ? 'badge-terminate' : 'badge-safe'}`}>
                        {inst.status === 'ZOMBIE' ? 'TERMINATE' : 'MONITOR'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </div>
  );
}

export default App;
