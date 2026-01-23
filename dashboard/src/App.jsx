import React, { useEffect, useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import mermaid from 'mermaid';
import { 
  Zap, 
  Target, 
  Activity, 
  AlertTriangle, 
  CheckCircle2,
  Clock,
  Box,
  Server,
  DollarSign,
  TrendingUp,
  Cpu,
  ArrowRight
} from 'lucide-react';
import './App.css';

// Initialize Mermaid
mermaid.initialize({
  startOnLoad: true,
  theme: 'dark',
  securityLevel: 'loose',
  fontFamily: 'Outfit',
  themeVariables: {
    primaryColor: '#00f2fe',
    lineColor: '#94a3b8',
    textColor: '#ffffff'
  }
});

const Mermaid = ({ chart }) => {
  const ref = useRef(null);

  useEffect(() => {
    if (ref.current && chart) {
      mermaid.render('mermaid-chart', chart).then((result) => {
        ref.current.innerHTML = result.svg;
      });
    }
  }, [chart]);

  return <div ref={ref} className="mermaid-wrapper" />;
};

const Gauge = ({ value, max = 100, label }) => {
  const percentage = Math.min((value / max) * 100, 100);
  const strokeDasharray = `${percentage} ${100 - percentage}`;

  return (
    <div className="hero-card stat-card">
      <div className="gauge-container">
        <svg viewBox="0 0 36 36" className="gauge-svg">
          <path className="gauge-bg" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
          <path className="gauge-fill" strokeDasharray={strokeDasharray} d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
        </svg>
      </div>
      <div className="hero-label">{label}</div>
      <div className="hero-value">{value}%</div>
    </div>
  );
};

function App() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const basePath = import.meta.env.BASE_URL.replace(/\/$/, "");
    const reportPath = `${basePath}/report.json`;
    
    fetch(reportPath)
      .then(res => {
        if (!res.ok) throw new Error(`HTTP Error: ${res.status}`);
        return res.json();
      })
      .then(d => {
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
      <motion.div 
        animate={{ opacity: [0.4, 1, 0.4] }}
        transition={{ repeat: Infinity, duration: 1.5 }}
        className="pulse-text"
      >
        CLOUDCULL // INITIALIZING...
      </motion.div>
    </div>
  );

  if (error || !data) return (
    <div className="error-screen">
      <AlertTriangle size={48} />
      <div style={{ marginTop: '1rem' }}>AUDIT DATA DISCONNECTED: {error || "No data"}</div>
    </div>
  );

  const sniperChart = `
    graph LR
      Probe[Probe: SDKs] --> Analyze[Analyze: AI]
      Analyze --> Decision{Decision}
      Decision -- "Zombie" --> Cull[Action: Cull]
      Decision -- "Healthy" --> Monitor[Monitor]
      Cull --> Sync[Report: Stats]
      Monitor --> Sync
      style Probe fill:transparent,stroke:#00f2fe,color:#fff
      style Analyze fill:transparent,stroke:#bd00ff,color:#fff
      style Decision fill:transparent,stroke:#f7b731,color:#fff
      style Cull fill:transparent,stroke:#ff2a6d,color:#fff
      style Monitor fill:transparent,stroke:#05f874,color:#fff
      style Sync fill:transparent,stroke:#00f2fe,color:#fff
  `;

  return (
    <div className="app-container">
      <motion.div 
        className="glass-panel main-dashboard"
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <header className="dashboard-header">
          <motion.div className="logo-container" whileHover={{ scale: 1.02 }}>
            <img src={`${basePath}/logo.png`} alt="CloudCull" className="brand-logo" />
          </motion.div>
          <div className="header-status">
            <span className="status-dot"></span> 
            <Activity size={14} className="pulse-icon" /> SERVICE ACTIVE
          </div>
        </header>

        <div className="executive-grid">
          <motion.div 
            className="hero-card main-hero"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.1 }}
          >
            <div className="hero-label">
              <DollarSign size={16} /> POTENTIAL MONTHLY RECOVERY
            </div>
            <div className="hero-value">
              ${data.summary.total_monthly_savings.toLocaleString(undefined, { minimumFractionDigits: 2 })}
            </div>
          </motion.div>

          <Gauge value={Math.round((data.summary.zombie_count / (data.instances.length || 1)) * 100)} label="Waste Efficiency" />

          <motion.div 
            className="hero-card stat-card"
            initial={{ opacity: 0, x: 10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.3 }}
          >
            <div className="hero-label"><TrendingUp size={16} /> PERFORMANCE IMPACT</div>
            <div className="hero-value">99.8%</div>
            <div className="hero-label">SYSTEM LATENCY: 12ms</div>
          </motion.div>
        </div>

        <section className="topology-container">
          <div className="topology-header">
            <Cpu size={18} color="#00f2fe" />
            <h3>AUTONOMOUS SNIPER TOPOLOGY</h3>
          </div>
          <Mermaid chart={sniperChart} />
        </section>

        <section className="cards-section">
          <div className="section-title">
            <h2><Zap size={18} /> DETECTED ANOMALIES</h2>
            <div className="anomaly-count">{data.instances.length} TARGETS ACQUIRED</div>
          </div>
          
          <div className="anomaly-grid">
            <AnimatePresence>
              {data.instances.map((inst, index) => (
                <motion.div 
                  key={inst.id}
                  className="anomaly-card"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.5 + index * 0.1 }}
                  whileHover={{ scale: 1.02 }}
                >
                  <div className="card-header">
                    <div className="platform-info">
                      <span className={`platform-badge ${inst.platform.toLowerCase()}-badge`}>
                        {inst.platform}
                      </span>
                      <span className="card-id">{inst.id}</span>
                      <span className="card-type">{inst.type}</span>
                    </div>
                    {inst.status === 'ZOMBIE' ? <AlertTriangle size={20} color="#ff2a6d" /> : <CheckCircle2 size={20} color="#05f874" />}
                  </div>

                  <div className="card-metrics">
                    <div className="metric-item">
                      <span className="metric-label">CPU LOAD</span>
                      <div className="metric-bar-bg">
                        <motion.div 
                          className="metric-bar-fill"
                          initial={{ width: 0 }}
                          animate={{ width: `${(inst.metrics.max_cpu / 100) * 100}%` }}
                          transition={{ duration: 1, delay: 0.8 }}
                        />
                      </div>
                    </div>
                    <div className="metric-item">
                      <span className="metric-label">NETWORK TX</span>
                      <div className="metric-bar-bg">
                        <motion.div 
                          className="metric-bar-fill" 
                          style={{ backgroundColor: '#bd00ff' }}
                          initial={{ width: 0 }}
                          animate={{ width: `${Math.min(inst.metrics.network_in * 10, 100)}%` }}
                          transition={{ duration: 1, delay: 0.9 }}
                        />
                      </div>
                    </div>
                  </div>

                  <div className="card-footer">
                    <div className="waste-info">
                      <span className="waste-amount">${(inst.rate * 24 * 30).toLocaleString()}</span>
                      <span className="owner-tag">BY @{inst.owner}</span>
                    </div>
                    <ArrowRight size={18} color="#94a3b8" />
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        </section>
      </motion.div>
    </div>
  );
}

export default App;
