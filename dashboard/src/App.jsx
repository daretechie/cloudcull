import React, { useEffect, useState, useRef, useId, useMemo } from 'react';
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
  ArrowRight,
  Terminal as TerminalIcon,
  ChevronUp,
  ChevronDown,
  Terminal,
  Copy,
  BrainCircuit,
  ShieldCheck
} from 'lucide-react';
import './App.css';

// Initialize Mermaid
mermaid.initialize({
  startOnLoad: false, // Set to false for manual rendering
  theme: 'dark',
  securityLevel: 'loose', // Needed for some SVG features
  fontFamily: 'system-ui, -apple-system, sans-serif', // Fallback to system fonts
  themeVariables: {
    primaryColor: '#00f2fe',
    lineColor: '#94a3b8',
    textColor: '#ffffff',
    fontSize: '12px'
  }
});

const Mermaid = ({ chart }) => {
  const ref = useRef(null);
  const chartId = useId().replace(/:/g, "");

  useEffect(() => {
    let isMounted = true;
    if (ref.current && chart) {
      // Small timeout to ensure DOM is ready for measurement
      const renderTimer = setTimeout(() => {
        if (!isMounted) return;
        
        try {
          ref.current.innerHTML = '';
          const uniqueId = `mermaid-${chartId}`;
          mermaid.render(uniqueId, chart).then((result) => {
            if (isMounted && ref.current) {
              ref.current.innerHTML = result.svg;
            }
          }).catch(err => {
            console.error("Mermaid render failed:", err);
            if (ref.current) ref.current.innerHTML = '<div class="diag-error">TOPOLOGY_LOAD_FAILED</div>';
          });
        } catch (err) {
          console.error("Mermaid critical error:", err);
        }
      }, 100);

      return () => {
        isMounted = false;
        clearTimeout(renderTimer);
      };
    }
  }, [chart, chartId]);

  return <div ref={ref} className="mermaid-wrapper" style={{ minHeight: '150px' }} />;
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

const SniperLog = ({ instances }) => {
  const [isOpen, setIsOpen] = useState(true);
  const [rawLogs, setRawLogs] = useState([]);
  const scrollRef = useRef(null);
  const basePath = import.meta.env.BASE_URL.replace(/\/$/, "");

  // Real Log Fetcher
  useEffect(() => {
    const fetchLogs = () => {
      fetch(`/api/logs`)
        .then(res => res.text())
        .then(text => {
          if (!text) return;
          const lines = text.split('\n')
            .filter(l => l.trim())
            .map(line => {
              const match = line.match(/^([\d-]+\s[\d:,]+)\s-\s\[CloudCull\]\s-\s(\w+)\s-\s(.+)$/);
              if (match) {
                return { time: match[1].split(' ')[1], tag: match[2], msg: match[3] };
              }
              return { time: '--:--:--', tag: 'INFO', msg: line };
            });
          setRawLogs(lines);
        })
        .catch(() => {}); // Silent fail for logs
    };

    fetchLogs();
    const interval = setInterval(fetchLogs, 2000);
    return () => clearInterval(interval);
  }, [basePath]);

  const displayLogs = React.useMemo(() => {
    if (rawLogs.length > 0) return rawLogs;
    if (instances.length > 0) {
      const baseLogs = [
        { time: new Date().toLocaleTimeString(), tag: "SYSTEM", msg: "CloudCull Engine initialized..." },
        { time: new Date().toLocaleTimeString(), tag: "PROBE",  msg: "Scanning AWS/Azure/GCP clusters..." },
      ];
      const instanceLogs = instances.map(inst => ({
        time: new Date().toLocaleTimeString(),
        tag: "SNIPER",
        msg: `Target ${inst.id.substring(0, 10)}... classified as ${inst.status}`
      }));
      return [...baseLogs, ...instanceLogs];
    }
    return [];
  }, [rawLogs, instances]);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [displayLogs]);

  return (
    <div className="sniper-log" style={{ height: isOpen ? 'auto' : '40px' }}>
      <div className="terminal-header" onClick={() => setIsOpen(!isOpen)}>
        <div className="terminal-title">
          <TerminalIcon size={14} /> SNIPER_CONSOLE_v1.07.EXE
        </div>
        {isOpen ? <ChevronDown size={14} /> : <ChevronUp size={14} />}
      </div>
      {isOpen && (
        <div className="terminal-body" ref={scrollRef}>
          {displayLogs.map((log, i) => (
            <div key={i} className="log-line">
              <span className="log-time">[{log.time}]</span>
              <span className="log-tag">{log.tag}:</span>
              <span className="log-msg">{log.msg}</span>
            </div>
          ))}
          <div className="log-line">
            <span className="log-tag">&gt;</span>
            <motion.span 
              animate={{ opacity: [1, 0] }} 
              transition={{ repeat: Infinity, duration: 0.8 }}
            >_</motion.span>
          </div>
        </div>
      )}
    </div>
  );
};

function App() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [copiedId, setCopiedId] = useState(null);

  const sniperChart = useMemo(() => `
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
  `, []);

  useEffect(() => {
    const basePath = import.meta.env.BASE_URL.replace(/\/$/, "");
    const reportPath = `/api/report`;
    
    const fetchData = () => {
      fetch(reportPath)
        .then(res => {
          if (!res.ok) throw new Error(`HTTP Error: ${res.status}`);
          return res.json();
        })
        .then(d => {
          setData(d);
          setLoading(false);
          setError(null); // Clear error on success
        })
        .catch(err => {
          console.error("Failed to load audit report:", err);
          // Only show error screen if we don't already have data (prevents flickering)
          if (!data) {
            setError(err.message);
            setLoading(false);
          }
        });
    };

    fetchData();
    const interval = setInterval(fetchData, 5000); // Poll every 5 seconds
    return () => clearInterval(interval);
  }, [data]);

  const copyCommand = (cmd, id) => {
    navigator.clipboard.writeText(cmd);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

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


  return (
    <div className="app-container">
      <motion.div 
        className="glass-panel main-dashboard"
        initial={{ opacity: 0, scale: 0.98 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5 }}
      >
        <header className="dashboard-header">
          <motion.div className="logo-container" whileHover={{ scale: 1.02 }}>
            <img 
              src={`${basePath}/logo.png`} 
              alt="CloudCull" 
              className="brand-logo" 
              onError={(e) => {
                e.target.style.display = 'none';
                e.target.parentNode.innerHTML = '<div class="fallback-logo">CLOUDCULL</div>';
              }}
            />
          </motion.div>
          
          <div className="header-meta">
            <div className="scan-timestamp">
              <Clock size={12} /> LAST SCAN: {new Date(data.summary.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </div>
            <div className="header-status">
              <span className="status-dot"></span> 
              <Activity size={14} className="pulse-icon" /> SNIPER ACTIVE
            </div>
          </div>
        </header>

        <div className="executive-grid">
          <motion.div 
            className="hero-card main-hero"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
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
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
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
            <h2><Zap size={18} /> TARGETS ACQUIRED</h2>
            <div className="anomaly-count">{data.instances.length} ANOMALIES DETECTED</div>
          </div>
          
          <div className="anomaly-grid">
            <AnimatePresence>
              {data.instances.map((inst, index) => (
                <motion.div 
                  key={inst.id}
                  className="anomaly-card"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.4 + (index % 10) * 0.05 }}
                  whileHover={{ scale: 1.02, borderColor: "var(--neon-blue)" }}
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

                  {inst.reasoning && (
                    <div className="sniper-reasoning">
                      <BrainCircuit size={14} style={{ marginBottom: '0.5rem', color: 'var(--neon-purple)' }} />
                      <div>{inst.reasoning}</div>
                    </div>
                  )}

                  <div className="card-metrics">
                    <div className="metric-item">
                      <span className="metric-label">CPU LOAD</span>
                      <div className="metric-bar-bg">
                        <motion.div 
                          className="metric-bar-fill"
                          initial={{ width: 0 }}
                          animate={{ width: `${(inst.metrics.max_cpu / 100) * 100}%` }}
                          transition={{ duration: 1, delay: 0.6 }}
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
                          transition={{ duration: 1, delay: 0.7 }}
                        />
                      </div>
                    </div>
                  </div>

                  <div className="card-footer">
                    <div className="waste-info">
                      <span className="owner-tag">LAUNCHED BY @{inst.owner}</span>
                      <span className="waste-amount">${(inst.rate * 24 * 30).toLocaleString()}</span>
                    </div>
                    <div className="snip-actions">
                      {inst.iac_command && (
                        <button 
                          id={`snip-button-${inst.id}`}
                          className="snip-button" 
                          title="Copy Kill Command"
                          onClick={() => copyCommand(inst.iac_command, inst.id)}
                        >
                          {copiedId === inst.id ? <ShieldCheck size={18} color="#05f874" /> : <Copy size={18} />}
                        </button>
                      )}
                      <ArrowRight size={18} color="#94a3b8" />
                    </div>
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        </section>
      </motion.div>
      <SniperLog instances={data.instances} />
    </div>
  );
}

export default App;
