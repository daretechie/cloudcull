import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
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
  TrendingUp
} from 'lucide-react';
import './App.css';

// Relaxed variants to ensure visibility even if stagger fails
const containerVariants = {
  hidden: { opacity: 0 },
  visible: { 
    opacity: 1,
    transition: { 
      duration: 0.4,
      staggerChildren: 0.1
    }
  }
};

const itemVariants = {
  hidden: { opacity: 0, y: 10 },
  visible: { 
    opacity: 1, 
    y: 0,
    transition: { duration: 0.5 }
  }
};

function App() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const basePath = import.meta.env.BASE_URL.replace(/\/$/, "");
    const reportPath = `${basePath}/report.json`;
    
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
        animate={{ opacity: [0.4, 1, 0.4] }}
        transition={{ repeat: Infinity, duration: 1.5 }}
      >
        CLOUDCULL // INITIALIZING...
      </motion.div>
    </div>
  );

  if (!data) return (
    <div className="error-screen">
      <AlertTriangle size={48} />
      <div>AUDIT DATA DISCONNECTED</div>
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
          <motion.div className="logo-container" variants={itemVariants}>
            <img src={`${basePath}/logo.png`} alt="CloudCull" className="brand-logo" />
          </motion.div>
          <motion.div className="header-status" variants={itemVariants}>
            <span className="status-dot"></span> 
            <Activity size={14} className="pulse-icon" /> SERVICE ACTIVE
          </motion.div>
        </header>

        <section className="hero-stats">
          <motion.div className="hero-card savings-card" variants={itemVariants}>
            <div className="hero-label">
              <DollarSign size={16} /> POTENTIAL MONTHLY RECOVERY
            </div>
            <div className="hero-value glowing-text">
              ${data.summary.total_monthly_savings.toLocaleString(undefined, { minimumFractionDigits: 2 })}
            </div>
          </motion.div>
        </section>

        <div className="secondary-stats">
          <motion.div className="stat-item" variants={itemVariants}>
            <span className="stat-label"><Box size={14} /> ZOMBIE NODES</span>
            <span className="stat-value text-zombie">{data.summary.zombie_count}</span>
          </motion.div>
          <motion.div className="stat-item" variants={itemVariants}>
            <span className="stat-label"><Server size={14} /> CLOUD PROBES</span>
            <span className="stat-value text-neon-blue">Active</span>
          </motion.div>
          <motion.div className="stat-item" variants={itemVariants}>
            <span className="stat-label"><Clock size={14} /> LAST SCAN</span>
            <span className="stat-value">{new Date(data.summary.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
          </motion.div>
        </div>

        <motion.section className="targets-section" variants={itemVariants}>
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
                <AnimatePresence>
                  {data.instances.map((inst, index) => (
                    <motion.tr 
                      key={inst.id}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ delay: 0.2 + index * 0.05 }}
                      whileHover={{ backgroundColor: "rgba(255,255,255,0.03)" }}
                    >
                      <td className="mono-font">{inst.id}</td>
                      <td>{inst.type}</td>
                      <td><span className="owner-tag">@{inst.owner}</span></td>
                      <td className="text-white font-bold">
                        ${(inst.rate * 24 * 30).toLocaleString()}
                      </td>
                      <td>
                        <span className={`status-badge-compact ${inst.status === 'ZOMBIE' ? 'badge-terminate' : 'badge-safe'}`}>
                          {inst.status === 'ZOMBIE' ? 'ZOMBIE' : 'ACTIVE'}
                        </span>
                      </td>
                    </motion.tr>
                  ))}
                </AnimatePresence>
              </tbody>
            </table>
          </div>
        </motion.section>
      </motion.div>
    </div>
  );
}

export default App;
