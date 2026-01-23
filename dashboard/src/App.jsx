import React, { useEffect, useState } from 'react';
import { 
  Zap, 
  Target, 
  Activity, 
  AlertTriangle, 
  CheckCircle2,
  Clock,
  Box,
  Server,
  DollarSign
} from 'lucide-react';
import './App.css';

function App() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    console.log("App mounted. Fetching report...");
    const basePath = import.meta.env.BASE_URL.replace(/\/$/, "");
    const reportPath = `${basePath}/report.json`;
    
    fetch(reportPath)
      .then(res => {
        if (!res.ok) throw new Error(`HTTP Error: ${res.status}`);
        return res.json();
      })
      .then(d => {
        console.log("Data loaded successfully:", d);
        setData(d);
        setLoading(false);
      })
      .catch(err => {
        console.error("Failed to load audit report:", err);
        setError(err.message);
        setLoading(false);
      });
  }, []);

  const basePath = import.meta.env.BASE_URL.replace(/\/$/, "");

  if (loading) return (
    <div className="loading-screen">
      <div className="pulse-text">CLOUDCULL // INITIALIZING...</div>
    </div>
  );

  if (error || !data) return (
    <div className="error-screen">
      <AlertTriangle size={48} />
      <div>AUDIT DATA DISCONNECTED: {error || "No data"}</div>
    </div>
  );

  return (
    <div className="app-container">
      <div className="glass-panel main-dashboard">
        <header className="dashboard-header">
          <div className="logo-container">
            <img src={`${basePath}/logo.png`} alt="CloudCull" className="brand-logo" />
          </div>
          <div className="header-status">
            <span className="status-dot"></span> 
            <Activity size={14} className="pulse-icon" /> SERVICE ACTIVE
          </div>
        </header>

        <section className="hero-stats">
          <div className="hero-card savings-card">
            <div className="hero-label">
              <DollarSign size={16} /> POTENTIAL MONTHLY RECOVERY
            </div>
            <div className="hero-value glowing-text">
              ${data.summary.total_monthly_savings.toLocaleString(undefined, { minimumFractionDigits: 2 })}
            </div>
          </div>
        </section>

        <div className="secondary-stats">
          <div className="stat-item">
            <span className="stat-label"><Box size={14} /> ZOMBIE NODES</span>
            <span className="stat-value text-zombie">{data.summary.zombie_count}</span>
          </div>
          <div className="stat-item">
            <span className="stat-label"><Server size={14} /> CLOUD PROBES</span>
            <span className="stat-value text-neon-blue">Active</span>
          </div>
          <div className="stat-item">
            <span className="stat-label"><Clock size={14} /> LAST SCAN</span>
            <span className="stat-value">
              {new Date(data.summary.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </span>
          </div>
        </div>

        <section className="targets-section">
          <div className="section-header">
            <h3><Zap size={16} /> TARGET ANOMALIES</h3>
            <span className="anomaly-count">{data.instances.length} NODES</span>
          </div>
          
          <div className="table-container">
            <table className="glass-table">
              <thead>
                <tr>
                  <th>INFRASTRUCTURE ID</th>
                  <th>TYPE</th>
                  <th>OWNER</th>
                  <th>WASTE / MO</th>
                  <th>STATUS</th>
                </tr>
              </thead>
              <tbody>
                {data.instances.map((inst, index) => (
                  <tr key={inst.id} className="table-row-static">
                    <td className="mono-font">{inst.id}</td>
                    <td>{inst.type}</td>
                    <td><span className="owner-tag">@{inst.owner}</span></td>
                    <td className="text-white font-bold">
                      ${(inst.rate * 24 * 30).toLocaleString()}
                    </td>
                    <td>
                      <span className={`status-badge-compact ${inst.status === 'ZOMBIE' ? 'badge-terminate' : 'badge-safe'}`}>
                        {inst.status === 'ZOMBIE' ? 'CULL' : 'SAFE'}
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
