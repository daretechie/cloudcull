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

import { motion, AnimatePresence } from 'framer-motion';
import { 
  Zap, 
  Target, 
  Activity, 
  ExternalLink, 
  AlertTriangle, 
  CheckCircle2,
  Clock,
  Box,
  Server
} from 'lucide-react';

const containerVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { 
    opacity: 1, 
    y: 0,
    transition: { 
      duration: 0.6,
      staggerChildren: 0.1
    }
  }
};

const itemVariants = {
  hidden: { opacity: 0, scale: 0.95 },
  visible: { opacity: 1, scale: 1 }
};

function App() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const reportPath = `${import.meta.env.BASE_URL.replace(/\/$/, "")}/report.json`;
    fetch(reportPath)
      .then(res => res.json())
      .then(d => {
        setData(d);
        setLoading(false);
      })
      .catch(err => {
        console.error("Failed to load audit report:", err);
        setLoading(false);
      });
  }, []);

  const basePath = import.meta.env.BASE_URL.replace(/\/$/, "");

  if (loading) return (
    <div className="loading-screen">
      <motion.div 
        animate={{ scale: [1, 1.1, 1], opacity: [0.5, 1, 0.5] }}
        transition={{ repeat: Infinity, duration: 2 }}
      >
        INITIALIZING CLOUDCULL PROTOCOL...
      </motion.div>
    </div>
  );

  if (!data) return (
    <div className="error-screen">
      <AlertTriangle className="error-icon" />
      NO AUDIT DATA DETECTED. EXECUTE SCAN.
    </div>
  );

  return (
    <div className="app-container">
      <motion.div 
        className="glass-panel main-dashboard"
        variants={containerVariants}
        initial="hidden"
        animate="visible"
      >
        <header className="dashboard-header">
          <motion.img 
            src={`${basePath}/logo.png`} 
            alt="CloudCull Logo" 
            className="brand-logo"
            whileHover={{ rotate: 5, scale: 1.05 }}
          />
          <div className="header-status">
            <span className="status-dot"></span> 
            <Activity size={14} className="pulse-icon" /> SYSTEM ONLINE
          </div>
        </header>

        <section className="hero-stats">
          <motion.div className="hero-card savings-card" variants={itemVariants}>
            <div className="hero-label"><Target size={14} inline /> POTENTIAL MONTHLY RECOVERY</div>
            <motion.div 
              className="hero-value glowing-text"
              initial={{ scale: 0.8 }}
              animate={{ scale: 1 }}
              transition={{ type: "spring", stiffness: 100 }}
            >
              ${data.summary.total_monthly_savings.toLocaleString(undefined, { minimumFractionDigits: 2 })}
            </motion.div>
          </motion.div>
        </section>

        <div className="secondary-stats">
          <motion.div className="stat-item" variants={itemVariants} whileHover={{ backgroundColor: "rgba(255,255,255,0.05)" }}>
            <span className="stat-label"><Box size={14} /> ZOMBIE NODES</span>
            <span className="stat-value text-zombie">{data.summary.zombie_count}</span>
          </motion.div>
          <motion.div className="stat-item" variants={itemVariants} whileHover={{ backgroundColor: "rgba(255,255,255,0.05)" }}>
            <span className="stat-label"><Server size={14} /> CLOUDS SCANNED</span>
            <span className="stat-value text-neon-blue">3</span>
          </motion.div>
          <motion.div className="stat-item" variants={itemVariants} whileHover={{ backgroundColor: "rgba(255,255,255,0.05)" }}>
            <span className="stat-label"><Clock size={14} /> LAST AUDIT</span>
            <span className="stat-value">{new Date(data.summary.timestamp).toLocaleTimeString()}</span>
          </motion.div>
        </div>

        <section className="targets-section">
          <div className="section-header">
            <h3><Zap size={16} /> DETECTED ANOMALIES</h3>
            <span className="anomaly-count">{data.instances.length} ACTIVE TARGETS</span>
          </div>
          
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
                <AnimatePresence>
                  {data.instances.map((inst, index) => (
                    <motion.tr 
                      key={inst.id}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.05 }}
                      whileHover={{ backgroundColor: "rgba(255,255,255,0.02)", x: 5 }}
                      className="table-row-interactive"
                    >
                      <td className="mono-font">{inst.id}</td>
                      <td>{inst.type}</td>
                      <td>
                        <span className="owner-tag">@{inst.owner}</span>
                      </td>
                      <td className="text-white font-semibold">
                        ${(inst.rate * 24 * 30).toLocaleString()}
                      </td>
                      <td>
                        <span className={`status-badge-compact ${inst.status === 'ZOMBIE' ? 'badge-terminate' : 'badge-safe'}`}>
                          {inst.status === 'ZOMBIE' ? <AlertTriangle size={12} /> : <CheckCircle2 size={12} />}
                          {inst.status === 'ZOMBIE' ? 'CULL' : 'MONITOR'}
                        </span>
                      </td>
                    </motion.tr>
                  ))}
                </AnimatePresence>
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </div>
  );
}

export default App;
