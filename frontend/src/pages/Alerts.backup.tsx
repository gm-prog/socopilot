import { useEffect, useMemo, useState } from 'react';
import '../styles/alerts-futuristic.css';

type Severity = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'INFO';
type AlertState = 'NEW' | 'ACKNOWLEDGED' | 'IN_PROGRESS' | 'ESCALATED' | 'CLOSED' | 'FALSE_POSITIVE';

type Ioc = { type: string; val: string; conf: number };
type TimelineStep = { t: string; txt: string; act?: boolean };
type Enrichment = { abuseipdb: string | null; virustotal: string | null; greynoise: string | null };

interface AlertItem {
  id: string;
  severity: Severity;
  title: string;
  source: string;
  entity: string;
  tactic: string;
  technique: string;
  detected: string;
  state: AlertState;
  analyst: string | null;
  correlations: number;
  risk: number;
  desc: string;
  iocs: Ioc[];
  timeline: TimelineStep[];
  enrichment: Enrichment;
}

const SEV_ORDER: Record<Severity, number> = {
  CRITICAL: 0,
  HIGH: 1,
  MEDIUM: 2,
  LOW: 3,
  INFO: 4,
};

const ANALYSTS: Record<string, { initials: string; color: string }> = {
  'A. Reed': { initials: 'AR', color: '#7c3aed' },
  'J. Chen': { initials: 'JC', color: '#2563eb' },
  'M. Okafor': { initials: 'MO', color: '#059669' },
  'S. Patel': { initials: 'SP', color: '#b45309' },
};

const ALERTS: AlertItem[] = [
  {
    id: 'ALT-20240528-001',
    severity: 'CRITICAL',
    title: 'Credential Dumping via LSASS Process Access',
    source: 'CrowdStrike',
    entity: 'WIN-PROD-001',
    tactic: 'Credential Access',
    technique: 'T1003.001 — LSASS Memory',
    detected: '21:43:12',
    state: 'IN_PROGRESS',
    analyst: 'A. Reed',
    correlations: 3,
    risk: 92,
    desc: 'Falcon sensor detected LSASS memory read by suspicious process mimikatz.exe. Process spawned under SYSTEM context from non-standard parent cmd.exe.',
    iocs: [
      { type: 'SHA256', val: 'e3b0c44298fc1c14', conf: 95 },
      { type: 'PROCESS', val: 'mimikatz.exe', conf: 98 },
      { type: 'HOST', val: 'WIN-PROD-001', conf: 100 },
    ],
    timeline: [
      { t: '21:43:12', txt: 'Falcon EDR detected LSASS memory access', act: true },
      { t: '21:43:15', txt: 'Process tree captured — parent: cmd.exe' },
      { t: '21:44:02', txt: 'Assigned to A. Reed for triage' },
      { t: '21:45:30', txt: 'Investigation in progress — awaiting memory dump' },
    ],
    enrichment: { abuseipdb: null, virustotal: '5/72 detections', greynoise: 'Not observed' },
  },
  {
    id: 'ALT-20240528-002',
    severity: 'CRITICAL',
    title: 'Shadow Copy Deletion — Ransomware Precursor Activity',
    source: 'CrowdStrike',
    entity: 'FILE-SRV-03',
    tactic: 'Impact',
    technique: 'T1490 — Inhibit System Recovery',
    detected: '21:38:55',
    state: 'ESCALATED',
    analyst: 'J. Chen',
    correlations: 0,
    risk: 96,
    desc: 'vssadmin.exe executed with delete shadows parameter. Consistent with pre-encryption stage of ransomware deployment.',
    iocs: [
      { type: 'CMD', val: 'vssadmin delete shadows /all', conf: 99 },
      { type: 'PROC', val: 'vssadmin.exe (SYSTEM)', conf: 97 },
    ],
    timeline: [
      { t: '21:38:55', txt: 'Shadow copy deletion command detected', act: true },
      { t: '21:39:01', txt: 'Alert escalated — potential ransomware' },
      { t: '21:39:20', txt: 'J. Chen investigating — host isolated' },
    ],
    enrichment: { abuseipdb: null, virustotal: null, greynoise: null },
  },
  {
    id: 'ALT-20240528-003',
    severity: 'HIGH',
    title: 'Lateral Movement via Pass-the-Hash Attack',
    source: 'Defender ATP',
    entity: 'WIN-DEV-027',
    tactic: 'Lateral Movement',
    technique: 'T1550.002 — Pass the Hash',
    detected: '21:35:41',
    state: 'ACKNOWLEDGED',
    analyst: 'A. Reed',
    correlations: 2,
    risk: 78,
    desc: 'Authentication event from non-interactive logon using NTLM hash. Source host WIN-DEV-027 is not a domain admin system.',
    iocs: [
      { type: 'IP', val: '10.20.1.27', conf: 85 },
      { type: 'ACCOUNT', val: 'svc-backup\\SYSTEM', conf: 90 },
    ],
    timeline: [
      { t: '21:35:41', txt: 'NTLM hash authentication detected', act: true },
      { t: '21:36:10', txt: 'Correlated with ALT-001 credential dump' },
      { t: '21:37:00', txt: 'Acknowledged by A. Reed' },
    ],
    enrichment: { abuseipdb: 'Not listed', virustotal: null, greynoise: 'Not observed' },
  },
  {
    id: 'ALT-20240528-004',
    severity: 'HIGH',
    title: 'Suspicious PowerShell Encoded Command Execution',
    source: 'SIEM',
    entity: 'WIN-HR-012',
    tactic: 'Execution',
    technique: 'T1059.001 — PowerShell',
    detected: '21:30:22',
    state: 'NEW',
    analyst: null,
    correlations: 0,
    risk: 71,
    desc: 'Encoded base64 PowerShell command executed by non-admin user. Command decodes to a web download cradle targeting an external IP.',
    iocs: [
      { type: 'URL', val: 'hxxp://194.165.16.11/stage2.ps1', conf: 88 },
      { type: 'CMD', val: 'powershell -enc JABz...', conf: 80 },
    ],
    timeline: [
      { t: '21:30:22', txt: 'Encoded PS execution detected', act: true },
      { t: '21:30:25', txt: 'Network connection attempt to 194.165.16.11' },
    ],
    enrichment: { abuseipdb: 'Reported 47 times', virustotal: '12/72 flagged', greynoise: 'Malicious' },
  },
  {
    id: 'ALT-20240528-005',
    severity: 'HIGH',
    title: 'C2 Beacon — Outbound to Known Malicious Infrastructure',
    source: 'NDR',
    entity: 'WIN-PROD-044',
    tactic: 'Command & Control',
    technique: 'T1071.001 — Web Protocols',
    detected: '21:28:17',
    state: 'NEW',
    analyst: null,
    correlations: 1,
    risk: 83,
    desc: 'Periodic HTTP beaconing to 194.165.16.11 every 60 seconds. Consistent with Cobalt Strike beacon profile. Jitter pattern matches known C2 framework.',
    iocs: [
      { type: 'IP', val: '194.165.16.11', conf: 94 },
      { type: 'DOMAIN', val: 'update-svc.net', conf: 91 },
      { type: 'PORT', val: '443/TCP', conf: 75 },
    ],
    timeline: [
      { t: '21:28:17', txt: 'First beacon detected', act: true },
      { t: '21:29:17', txt: 'Second beacon — 60s interval confirmed' },
      { t: '21:30:17', txt: 'Third beacon — C2 profile match' },
    ],
    enrichment: { abuseipdb: 'Reported 214 times', virustotal: '48/72 flagged', greynoise: 'Malicious — Cobalt Strike' },
  },
  {
    id: 'ALT-20240528-006',
    severity: 'HIGH',
    title: 'Token Impersonation for Privilege Escalation',
    source: 'CrowdStrike',
    entity: 'WIN-EXEC-007',
    tactic: 'Privilege Escalation',
    technique: 'T1134.001 — Token Impersonation',
    detected: '21:25:08',
    state: 'ACKNOWLEDGED',
    analyst: 'M. Okafor',
    correlations: 0,
    risk: 69,
    desc: 'svc-backup service account token was duplicated and used to spawn a high-integrity shell under the context of a domain admin account.',
    iocs: [
      { type: 'ACCOUNT', val: 'domain\\svc-backup', conf: 88 },
      { type: 'HOST', val: 'WIN-EXEC-007', conf: 100 },
    ],
    timeline: [
      { t: '21:25:08', txt: 'Token duplication event detected', act: true },
      { t: '21:26:00', txt: 'High-integrity shell spawned' },
      { t: '21:27:30', txt: 'Acknowledged by M. Okafor' },
    ],
    enrichment: { abuseipdb: null, virustotal: null, greynoise: null },
  },
  {
    id: 'ALT-20240528-007',
    severity: 'MEDIUM',
    title: 'SSH Brute Force — 847 Attempts in 5 Minutes',
    source: 'WAF',
    entity: 'LINUX-WEB-02',
    tactic: 'Credential Access',
    technique: 'T1110.001 — Password Guessing',
    detected: '21:20:44',
    state: 'ACKNOWLEDGED',
    analyst: 'S. Patel',
    correlations: 0,
    risk: 52,
    desc: 'Inbound SSH brute force from IP 45.83.193.12. 847 authentication failures in a 5-minute window against root and ubuntu accounts.',
    iocs: [
      { type: 'IP', val: '45.83.193.12', conf: 99 },
      { type: 'PORT', val: '22/TCP', conf: 100 },
    ],
    timeline: [
      { t: '21:20:44', txt: 'Brute force threshold breached', act: true },
      { t: '21:21:00', txt: 'IP blocked at perimeter WAF' },
      { t: '21:22:00', txt: 'Acknowledged by S. Patel' },
    ],
    enrichment: { abuseipdb: 'Reported 831 times', virustotal: '39/72 flagged', greynoise: 'Scanning — Brute force' },
  },
  {
    id: 'ALT-20240528-008',
    severity: 'MEDIUM',
    title: 'Suspicious Registry Run Key Modification',
    source: 'Defender ATP',
    entity: 'WIN-DEV-041',
    tactic: 'Persistence',
    technique: 'T1547.001 — Registry Run Keys',
    detected: '21:18:03',
    state: 'NEW',
    analyst: null,
    correlations: 0,
    risk: 48,
    desc: 'New registry key added to HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run by non-admin user. Points to a temp directory executable.',
    iocs: [
      { type: 'REG_KEY', val: 'HKCU\\...\\Run\\UpdateSvc', conf: 82 },
      { type: 'PATH', val: 'C:\\Users\\jdoe\\AppData\\Temp\\upd.exe', conf: 90 },
    ],
    timeline: [{ t: '21:18:03', txt: 'Registry modification detected', act: true }],
    enrichment: { abuseipdb: null, virustotal: '2/72 detections', greynoise: null },
  },
  {
    id: 'ALT-20240528-009',
    severity: 'MEDIUM',
    title: 'Large Data Transfer to External IP — Possible Exfiltration',
    source: 'DLP',
    entity: 'WIN-FIN-003',
    tactic: 'Exfiltration',
    technique: 'T1048 — Exfiltration Over Alt Protocol',
    detected: '21:14:39',
    state: 'IN_PROGRESS',
    analyst: 'J. Chen',
    correlations: 0,
    risk: 61,
    desc: '2.4 GB outbound transfer to 198.51.100.44 over port 443. Source host belongs to Finance team. Transfer occurred outside business hours.',
    iocs: [
      { type: 'IP', val: '198.51.100.44', conf: 70 },
      { type: 'BYTES', val: '2.4 GB outbound', conf: 100 },
    ],
    timeline: [
      { t: '21:14:39', txt: 'DLP threshold exceeded', act: true },
      { t: '21:15:00', txt: 'Transfer ongoing — endpoint blocked' },
      { t: '21:16:30', txt: 'J. Chen investigating data classification' },
    ],
    enrichment: { abuseipdb: 'Not reported', virustotal: null, greynoise: 'Not observed' },
  },
  {
    id: 'ALT-20240528-010',
    severity: 'MEDIUM',
    title: 'Admin Share Access from Non-Administrative Workstation',
    source: 'SIEM',
    entity: 'WIN-IT-019',
    tactic: 'Lateral Movement',
    technique: 'T1021.002 — SMB/Windows Admin Shares',
    detected: '21:10:17',
    state: 'NEW',
    analyst: null,
    correlations: 1,
    risk: 44,
    desc: 'Non-admin workstation WIN-IT-019 accessed C$ share on FILE-SRV-03. Account j.smith does not have documented access to file server admin shares.',
    iocs: [
      { type: 'ACCOUNT', val: 'DOMAIN\\j.smith', conf: 85 },
      { type: 'SHARE', val: '\\\\FILE-SRV-03\\C$', conf: 100 },
    ],
    timeline: [{ t: '21:10:17', txt: 'Admin share access event correlated', act: true }],
    enrichment: { abuseipdb: null, virustotal: null, greynoise: null },
  },
  {
    id: 'ALT-20240528-011',
    severity: 'MEDIUM',
    title: 'Local Admin Account Created Outside Change Window',
    source: 'SIEM',
    entity: 'WIN-DEV-033',
    tactic: 'Persistence',
    technique: 'T1136.001 — Local Account',
    detected: '21:05:52',
    state: 'FALSE_POSITIVE',
    analyst: 'S. Patel',
    correlations: 0,
    risk: 30,
    desc: 'New local administrator account "svc-deploy" created on WIN-DEV-033 at 21:05 UTC, outside approved change window (07:00–19:00 UTC).',
    iocs: [{ type: 'ACCOUNT', val: 'WIN-DEV-033\\svc-deploy', conf: 75 }],
    timeline: [
      { t: '21:05:52', txt: 'New local admin account detected', act: true },
      { t: '21:08:00', txt: 'Verified with DevOps — legitimate deployment account' },
      { t: '21:09:00', txt: 'Marked false positive by S. Patel' },
    ],
    enrichment: { abuseipdb: null, virustotal: null, greynoise: 'Not observed' },
  },
  {
    id: 'ALT-20240528-012',
    severity: 'LOW',
    title: 'Network Port Scan Detected from Internal Host',
    source: 'NDR',
    entity: 'LINUX-DB-01',
    tactic: 'Discovery',
    technique: 'T1046 — Network Service Scanning',
    detected: '21:02:34',
    state: 'ACKNOWLEDGED',
    analyst: 'M. Okafor',
    correlations: 0,
    risk: 22,
    desc: 'nmap SYN scan detected originating from LINUX-DB-01 targeting 254 hosts on port 22, 80, 443. Scan duration: 4 minutes.',
    iocs: [
      { type: 'IP', val: '10.10.5.44', conf: 100 },
      { type: 'TOOL', val: 'nmap (inferred)', conf: 60 },
    ],
    timeline: [
      { t: '21:02:34', txt: 'Port scan activity threshold breached', act: true },
      { t: '21:03:00', txt: 'Acknowledged — suspected authorized scan' },
    ],
    enrichment: { abuseipdb: null, virustotal: null, greynoise: null },
  },
  {
    id: 'ALT-20240528-013',
    severity: 'LOW',
    title: 'Repeated MFA Failures Exceeding Threshold',
    source: 'IdP',
    entity: 'user: j.chen@acme.com',
    tactic: 'Credential Access',
    technique: 'T1110.002 — Password Spraying',
    detected: '20:58:11',
    state: 'CLOSED',
    analyst: 'A. Reed',
    correlations: 0,
    risk: 18,
    desc: 'MFA push notification declined 11 times within 30 minutes for user j.chen@acme.com. Possible MFA fatigue attack or compromised credentials.',
    iocs: [
      { type: 'ACCOUNT', val: 'j.chen@acme.com', conf: 100 },
      { type: 'IP', val: '91.134.209.70', conf: 80 },
    ],
    timeline: [
      { t: '20:58:11', txt: 'MFA failure threshold breached', act: true },
      { t: '21:00:00', txt: 'User contacted — confirmed MFA fatigue attempt' },
      { t: '21:05:00', txt: 'Account secured — closed by A. Reed' },
    ],
    enrichment: { abuseipdb: 'Reported 3 times', virustotal: null, greynoise: 'Not observed' },
  },
  {
    id: 'ALT-20240528-014',
    severity: 'LOW',
    title: 'DNS Query to Known Malware Distribution Domain',
    source: 'DNS Filter',
    entity: 'WIN-ACCT-022',
    tactic: 'Command & Control',
    technique: 'T1071.004 — DNS',
    detected: '20:52:43',
    state: 'CLOSED',
    analyst: 'M. Okafor',
    correlations: 0,
    risk: 35,
    desc: 'DNS query for "cdn-update-patch.biz" blocked by DNS security layer. Domain categorised as malware distribution. Query originated from WIN-ACCT-022.',
    iocs: [
      { type: 'DOMAIN', val: 'cdn-update-patch.biz', conf: 97 },
      { type: 'HOST', val: 'WIN-ACCT-022', conf: 100 },
    ],
    timeline: [
      { t: '20:52:43', txt: 'Malicious DNS query blocked', act: true },
      { t: '20:54:00', txt: 'Endpoint scan initiated — clean' },
      { t: '20:58:00', txt: 'Closed — DNS block sufficient' },
    ],
    enrichment: { abuseipdb: 'Reported 144 times', virustotal: '61/72 flagged', greynoise: 'Malicious' },
  },
  {
    id: 'ALT-20240528-015',
    severity: 'INFO',
    title: 'Authorized Vulnerability Scanner Activity',
    source: 'NDR',
    entity: 'scan-host-01',
    tactic: 'Discovery',
    technique: 'T1595 — Active Scanning',
    detected: '20:45:00',
    state: 'CLOSED',
    analyst: 'S. Patel',
    correlations: 0,
    risk: 5,
    desc: 'Scheduled Nessus vulnerability scan detected and classified. Source IP 10.10.0.50 is registered as an authorized scanner in the asset inventory.',
    iocs: [{ type: 'IP', val: '10.10.0.50', conf: 100 }],
    timeline: [
      { t: '20:45:00', txt: 'Scan activity detected', act: true },
      { t: '20:45:30', txt: 'Source matched authorized scanner list' },
      { t: '20:46:00', txt: 'Auto-classified and closed' },
    ],
    enrichment: { abuseipdb: null, virustotal: null, greynoise: null },
  },
];

type SortKey = 'severity' | 'id' | 'entity' | 'detected';

function formatStateLabel(state: AlertState) {
  return state.replace('_', ' ');
}

export default function AlertsPage() {
  const [sevFilter, setSevFilter] = useState<'ALL' | Severity>('ALL');
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [selectedRows, setSelectedRows] = useState<Set<string>>(new Set());
  const [sortKey, setSortKey] = useState<SortKey>('detected');
  const [sortDir, setSortDir] = useState<1 | -1>(-1);
  const [searchQuery, setSearchQuery] = useState('');
  const [stateFilter, setStateFilter] = useState('');
  const [rate, setRate] = useState<number>(Math.floor(Math.random() * 200 + 400));

  useEffect(() => {
    const interval = window.setInterval(() => setRate(Math.floor(Math.random() * 200 + 400)), 3000);
    return () => window.clearInterval(interval);
  }, []);

  const filteredAlerts = useMemo(() => {
    const term = searchQuery.toLowerCase();
    return ALERTS.filter((alert) => {
      const matchesSeverity = sevFilter === 'ALL' || alert.severity === sevFilter;
      const matchesState = !stateFilter || alert.state === stateFilter;
      const matchesSearch =
        !term ||
        alert.title.toLowerCase().includes(term) ||
        alert.id.toLowerCase().includes(term) ||
        alert.entity.toLowerCase().includes(term) ||
        alert.source.toLowerCase().includes(term) ||
        alert.tactic.toLowerCase().includes(term);
      return matchesSeverity && matchesState && matchesSearch;
    }).sort((a, b) => {
      if (sortKey === 'severity') return (SEV_ORDER[a.severity] - SEV_ORDER[b.severity]) * sortDir;
      if (sortKey === 'id') return a.id.localeCompare(b.id) * sortDir;
      if (sortKey === 'entity') return a.entity.localeCompare(b.entity) * sortDir;
      return sortDir === 1 ? a.detected.localeCompare(b.detected) : b.detected.localeCompare(a.detected);
    });
  }, [sevFilter, stateFilter, searchQuery, sortKey, sortDir]);

  const counts = useMemo(() => {
    const c: Record<'ALL' | Severity, number> = { ALL: ALERTS.length, CRITICAL: 0, HIGH: 0, MEDIUM: 0, LOW: 0, INFO: 0 };
    ALERTS.forEach((alert) => {
      c[alert.severity] += 1;
    });
    return c;
  }, []);

  const selectedAlert = useMemo(() => ALERTS.find((alert) => alert.id === selectedId) ?? null, [selectedId]);
  const criticalOpen = ALERTS.filter((alert) => alert.severity === 'CRITICAL' && alert.state !== 'CLOSED' && alert.state !== 'FALSE_POSITIVE').length;
  const openAlerts = ALERTS.filter((alert) => alert.state !== 'CLOSED' && alert.state !== 'FALSE_POSITIVE').length;

  const toggleRow = (id: string, checked: boolean) => {
    setSelectedRows((current) => {
      const next = new Set(current);
      if (checked) next.add(id);
      else next.delete(id);
      return next;
    });
  };

  const toggleAll = (checked: boolean) => {
    setSelectedRows(() => {
      if (!checked) return new Set();
      return new Set(filteredAlerts.map((alert) => alert.id));
    });
  };

  const clearSelection = () => setSelectedRows(new Set());
  const selectRow = (id: string) => setSelectedId((current) => (current === id ? null : id));
  const batchAction = (_action: string) => setSelectedRows(new Set());

  const renderIocs = (iocs: Ioc[]) =>
    iocs.map((ioc) => (
      <tr key={`${ioc.type}-${ioc.val}`}>
        <td className="ioc-type">{ioc.type}</td>
        <td className="ioc-val">{ioc.val}</td>
        <td className="ioc-conf">
          <span className={ioc.conf >= 85 ? 'conf-h' : ioc.conf >= 60 ? 'conf-m' : 'conf-l'}>{ioc.conf}%</span>
        </td>
      </tr>
    ));

  const renderTimeline = (timeline: TimelineStep[]) =>
    timeline.map((step) => (
      <div key={`${step.t}-${step.txt}`} className="tl-row">
        <div className="tl-time">{step.t}</div>
        <div className={`tl-dot ${step.act ? 'active' : ''}`} />
        <div className="tl-text">{step.txt}</div>
      </div>
    ));

  const selectedCount = selectedRows.size;
  const selectAllChecked = filteredAlerts.length > 0 && selectedCount === filteredAlerts.length;

  return (
    <div className="shell">
      <header>
        <div className="hd-brand">
          <div className="hd-logo"><i className="ti ti-shield-bolt" /></div>
          <span className="hd-name">SOCopilot</span>
          <span className="hd-sep">/</span>
          <span className="hd-org">Acme Corp</span>
        </div>
        <nav className="hd-nav">
          <button type="button" className="hn-btn"><i className="ti ti-layout-dashboard" /> Dashboard</button>
          <button type="button" className="hn-btn active"><i className="ti ti-bell-ringing" /> Alerts</button>
          <button type="button" className="hn-btn"><i className="ti ti-folder-open" /> Cases</button>
          <button type="button" className="hn-btn"><i className="ti ti-search" /> Investigate</button>
        </nav>
        <div className="hd-stats">
          <div className="hstat"><div className="hs-val r">{openAlerts}</div><div className="hs-lbl">Open Alerts</div></div>
          <div className="hd-vsep" />
          <div className="hstat"><div className="hs-val r">{criticalOpen}</div><div className="hs-lbl">Critical</div></div>
          <div className="hd-vsep" />
          <div className="hstat"><div className="hs-val g">99.8%</div><div className="hs-lbl">Pipeline Health</div></div>
          <div className="hd-vsep" />
          <div className="hstat"><div className="hs-val">{rate}</div><div className="hs-lbl">Events / sec</div></div>
        </div>
        <div className="hd-right">
          <div className="live-badge"><div className="live-dot" /><span className="live-txt">LIVE</span></div>
          <button type="button" className="hd-btn has-tip" data-tip="Notifications"><i className="ti ti-bell" /><span className="nb" /></button>
          <button type="button" className="hd-btn has-tip" data-tip="Settings"><i className="ti ti-settings" /></button>
          <div className="avatar">JS</div>
        </div>
      </header>

      <div className="body">
        <nav className="sidebar">
          <button type="button" className="sb-btn" title="Dashboard"><i className="ti ti-layout-dashboard" /><span className="tt">Dashboard</span></button>
          <button type="button" className="sb-btn active" title="Alert Queue"><i className="ti ti-bell-ringing" /><span className="tt">Alert Queue</span></button>
          <button type="button" className="sb-btn" title="Cases"><i className="ti ti-folder-open" /><span className="tt">Cases</span></button>
          <div className="sb-sep" />
          <button type="button" className="sb-btn" title="Investigate"><i className="ti ti-timeline-event" /><span className="tt">Investigate</span></button>
          <button type="button" className="sb-btn" title="Telemetry"><i className="ti ti-chart-line" /><span className="tt">Telemetry</span></button>
          <button type="button" className="sb-btn" title="AI Copilot"><i className="ti ti-robot" /><span className="tt">AI Copilot</span></button>
          <div className="sb-sep" />
          <button type="button" className="sb-btn" title="Analysts"><i className="ti ti-users" /><span className="tt">Analysts</span></button>
          <div className="sb-sp" />
          <button type="button" className="sb-btn" title="Settings"><i className="ti ti-settings" /><span className="tt">Settings</span></button>
        </nav>

        <div className="content">
          <div className="toolbar" id="toolbar">
            <span className="page-title">Alert Queue</span>
            <span className="new-badge" style={{ display: 'none' }}>● NEW</span>
            <div className="tb-sep" />
            <div className="filter-chips">
              {(['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'] as const).map((level) => (
                <button
                  key={level}
                  type="button"
                  className={`chip ${level === 'CRITICAL' ? 'c-crit' : level === 'HIGH' ? 'c-high' : level === 'MEDIUM' ? 'c-med' : level === 'LOW' ? 'c-low' : ''} ${sevFilter === level ? 'active' : ''}`}
                  onClick={() => setSevFilter(level)}
                >
                  {level === 'ALL' ? 'All' : level.charAt(0) + level.slice(1).toLowerCase()}
                  <span className="chip-n">{counts[level]}</span>
                </button>
              ))}
            </div>
            <div className="tb-sep" />
            <select value={stateFilter} onChange={(event) => setStateFilter(event.target.value)} className="state-select">
              <option value="">All States</option>
              <option value="NEW">New</option>
              <option value="ACKNOWLEDGED">Acknowledged</option>
              <option value="IN_PROGRESS">In Progress</option>
              <option value="ESCALATED">Escalated</option>
              <option value="CLOSED">Closed</option>
            </select>
            <div className="tb-sp" />
            <div className="search-box">
              <i className="ti ti-search" />
              <input value={searchQuery} onChange={(event) => setSearchQuery(event.target.value)} placeholder="Search alerts, entities, IDs..." />
            </div>
            <button type="button" className="tb-btn"><i className="ti ti-columns" /> Columns</button>
            <button type="button" className="tb-btn"><i className="ti ti-download" /> Export</button>
          </div>

          <div className={`batch-bar ${selectedCount > 0 ? 'show' : ''}`} id="batch-bar">
            <span className="bc-label"><span id="sel-count">{selectedCount}</span> alerts selected</span>
            <div className="bc-actions">
              <button type="button" className="ba" onClick={() => batchAction('assign')}><i className="ti ti-user-plus" /> Assign</button>
              <button type="button" className="ba" onClick={() => batchAction('ack')}><i className="ti ti-check" /> Acknowledge</button>
              <button type="button" className="ba" onClick={() => batchAction('close')}><i className="ti ti-x" /> Close</button>
              <button type="button" className="ba" onClick={() => batchAction('case')}><i className="ti ti-folder-plus" /> Create Case</button>
              <button type="button" className="ba danger" onClick={() => batchAction('fp')}><i className="ti ti-thumb-down" /> False Positive</button>
            </div>
            <button type="button" className="ba" onClick={clearSelection}><i className="ti ti-x" /></button>
          </div>

          <div className="table-area" id="table-area">
            <div style={{ display: 'flex', flexDirection: 'column', overflow: 'hidden', minHeight: 0 }}>
              <div className="table-wrap" id="table-wrap">
                <table id="alert-table">
                  <thead>
                    <tr>
                      <th className="col-chk"><input type="checkbox" checked={selectAllChecked} onChange={(event) => toggleAll(event.target.checked)} /></th>
                      <th className={`col-sev ${sortKey === 'severity' ? 'sorted' : ''}`} onClick={() => { setSortKey('severity'); setSortDir(sortDir === 1 ? -1 : 1); }}><div className="th-i">SEV<i className="ti ti-selector sort-ic" /></div></th>
                      <th className={`col-id ${sortKey === 'id' ? 'sorted' : ''}`} onClick={() => { setSortKey('id'); setSortDir(sortDir === 1 ? -1 : 1); }}><div className="th-i">ALERT ID<i className="ti ti-selector sort-ic" /></div></th>
                      <th className="col-title"><div className="th-i">TITLE</div></th>
                      <th className="col-src"><div className="th-i">SOURCE</div></th>
                      <th className={`col-entity ${sortKey === 'entity' ? 'sorted' : ''}`} onClick={() => { setSortKey('entity'); setSortDir(sortDir === 1 ? -1 : 1); }}><div className="th-i">ENTITY<i className="ti ti-selector sort-ic" /></div></th>
                      <th className="col-tactic"><div className="th-i">TACTIC</div></th>
                      <th className={`col-time ${sortKey === 'detected' ? 'sorted' : ''}`} onClick={() => { setSortKey('detected'); setSortDir(sortDir === 1 ? -1 : 1); }}><div className="th-i">DETECTED<i className="ti ti-selector sort-ic" /></div></th>
                      <th className="col-state"><div className="th-i">STATE</div></th>
                      <th className="col-analyst"><div className="th-i">ANALYST</div></th>
                      <th className="col-act" />
                    </tr>
                  </thead>
                  <tbody>
                    {filteredAlerts.map((alert) => {
                      const rowSelected = selectedId === alert.id;
                      return (
                        <tr key={alert.id} data-s={alert.severity} className={rowSelected ? 'sel' : ''} onClick={() => selectRow(alert.id)}>
                          <td className="col-chk" onClick={(event) => event.stopPropagation()}>
                            <input type="checkbox" checked={selectedRows.has(alert.id)} onChange={(event) => toggleRow(alert.id, event.target.checked)} />
                          </td>
                          <td className="col-sev sev-cell"><div className="sev-inner"><span className={`sev-pill ${alert.severity}`}>{alert.severity}</span></div></td>
                          <td className="col-id"><span className="mono">{alert.id}</span></td>
                          <td className="col-title"><div className="title-wrap"><span className="title-txt">{alert.title}</span>{alert.correlations > 0 ? <span className="corr-tag">+{alert.correlations}</span> : null}</div></td>
                          <td className="col-src"><span className="src-pill">{alert.source}</span></td>
                          <td className="col-entity"><span className="mono">{alert.entity}</span></td>
                          <td className="col-tactic"><span className="tactic-pill">{alert.tactic}</span></td>
                          <td className="col-time"><span className="mono">{alert.detected}</span></td>
                          <td className="col-state"><span className={`state-pill st-${alert.state}`}>{formatStateLabel(alert.state)}</span></td>
                          <td className="col-analyst">{alert.analyst ? <div className="analyst-wrap"><div className="analyst-av" style={{ background: ANALYSTS[alert.analyst]?.color || '#555' }}>{ANALYSTS[alert.analyst]?.initials || '?'}</div><span className="analyst-name">{alert.analyst.split(' ')[1]}</span></div> : <span className="unassigned">Unassigned</span>}</td>
                          <td className="col-act"><div className="act-wrap"><button type="button" className="act-ic has-tip" data-tip="Acknowledge"><i className="ti ti-check" /></button><button type="button" className="act-ic has-tip" data-tip="More"><i className="ti ti-dots" /></button></div></td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
              <div className="statusbar">
                <div className="sb-item ok"><i className="ti ti-circle-check" /> Pipeline connected</div>
                <div className="sb-item"><i className="ti ti-database" /> <span className="sb-showing">{filteredAlerts.length} of {ALERTS.length}</span> alerts</div>
                <div className="sb-item r"><i className="ti ti-alert-triangle" /> <span className="sb-crit">{criticalOpen}</span> critical unacknowledged</div>
                <div className="sb-sp2" />
                <div className="sb-pager"><button type="button" className="pg-b"><i className="ti ti-chevron-left" /></button><span className="pg-label">Page 1 / 1</span><button type="button" className="pg-b"><i className="ti ti-chevron-right" /></button></div>
              </div>
            </div>

            <div className="dp" id="detail-panel">
              {!selectedAlert ? (
                <div className="dp-empty">
                  <i className="ti ti-list-search" />
                  <div className="dp-empty-t">No alert selected</div>
                  <div className="dp-empty-s">Click any row to inspect the alert, view enrichment data, and take action.</div>
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', overflow: 'hidden', minHeight: 0 }}>
                  <div className="dp-hdr">
                    <div className="dp-top">
                      <div className="dp-title">{selectedAlert.title}</div>
                      <button type="button" className="dp-close" onClick={() => setSelectedId(null)}><i className="ti ti-x" /></button>
                    </div>
                    <div className="dp-meta">
                      <span className={`sev-pill ${selectedAlert.severity}`} style={{ fontSize: '9px' }}>{selectedAlert.severity}</span>
                      <span className="dp-id">{selectedAlert.id}</span>
                      <span className={`state-pill st-${selectedAlert.state}`} style={{ fontSize: '9px' }}>{formatStateLabel(selectedAlert.state)}</span>
                    </div>
                  </div>
                  <div className="dp-acts">
                    <button type="button" className="dp-act primary"><i className="ti ti-user-plus" /> Assign</button>
                    <button type="button" className="dp-act"><i className="ti ti-check" /> Ack</button>
                    <button type="button" className="dp-act"><i className="ti ti-folder-plus" /> Case</button>
                    <button type="button" className="dp-act"><i className="ti ti-bolt" /> Respond</button>
                  </div>
                  <div className="dp-body">
                    <div className="dp-sec">
                      <div className="dp-sec-lbl">Overview</div>
                      <div className="kv-grid" style={{ marginBottom: '8px' }}>
                        <div className="kv"><div className="k">Source</div><div className="v">{selectedAlert.source}</div></div>
                        <div className="kv"><div className="k">Entity</div><div className="v">{selectedAlert.entity}</div></div>
                        <div className="kv"><div className="k">Detected</div><div className="v">{selectedAlert.detected}</div></div>
                        <div className="kv"><div className="k">Analyst</div><div className="v dim">{selectedAlert.analyst ?? 'Unassigned'}</div></div>
                      </div>
                      <div style={{ marginBottom: '4px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ fontSize: '9px', color: 'var(--t-3)', textTransform: 'uppercase', letterSpacing: '0.07em' }}>Risk Score</span>
                        <span style={{ fontFamily: 'var(--ff-data)', fontSize: '9px', color: selectedAlert.risk >= 80 ? 'var(--crit)' : selectedAlert.risk >= 60 ? 'var(--high)' : selectedAlert.risk >= 40 ? 'var(--med)' : 'var(--state-cls)' }}>{selectedAlert.risk >= 80 ? 'CRITICAL' : selectedAlert.risk >= 60 ? 'HIGH' : selectedAlert.risk >= 40 ? 'MEDIUM' : 'LOW'}</span>
                      </div>
                      <div className="risk-row">
                        <div className="risk-track"><div className="risk-fill" style={{ width: `${selectedAlert.risk}%`, background: selectedAlert.risk >= 80 ? 'var(--crit)' : selectedAlert.risk >= 60 ? 'var(--high)' : selectedAlert.risk >= 40 ? 'var(--med)' : 'var(--state-cls)' }} /></div>
                        <div className="risk-label" style={{ color: selectedAlert.risk >= 80 ? 'var(--crit)' : selectedAlert.risk >= 60 ? 'var(--high)' : selectedAlert.risk >= 40 ? 'var(--med)' : 'var(--state-cls)' }}>{selectedAlert.risk}</div>
                      </div>
                      <div style={{ marginTop: '10px', fontSize: '11px', color: 'var(--t-2)', lineHeight: 1.5 }}>{selectedAlert.desc}</div>
                    </div>
                    <div className="dp-sec">
                      <div className="dp-sec-lbl">MITRE ATT&CK</div>
                      <div className="mitre-card">
                        <div className="mitre-half"><div className="mitre-lbl">Tactic</div><div className="mitre-val">{selectedAlert.tactic}</div></div>
                        <div className="mitre-half"><div className="mitre-lbl">Technique</div><div className="mitre-val" style={{ fontSize: '10px' }}>{selectedAlert.technique}</div></div>
                      </div>
                    </div>
                    <div className="dp-sec">
                      <div className="dp-sec-lbl">Indicators of Compromise</div>
                      <table className="ioc-tbl">{renderIocs(selectedAlert.iocs)}</table>
                    </div>
                    <div className="dp-sec">
                      <div className="dp-sec-lbl">Enrichment</div>
                      {selectedAlert.enrichment.abuseipdb || selectedAlert.enrichment.virustotal || selectedAlert.enrichment.greynoise ? (
                        <div className="kv-grid">
                          {selectedAlert.enrichment.abuseipdb ? <div className="kv"><div className="k">AbuseIPDB</div><div className="v dim">{selectedAlert.enrichment.abuseipdb}</div></div> : null}
                          {selectedAlert.enrichment.virustotal ? <div className="kv"><div className="k">VirusTotal</div><div className="v dim">{selectedAlert.enrichment.virustotal}</div></div> : null}
                          {selectedAlert.enrichment.greynoise ? <div className="kv"><div className="k">GreyNoise</div><div className="v dim">{selectedAlert.enrichment.greynoise}</div></div> : null}
                        </div>
                      ) : (
                        <div style={{ fontSize: '10px', color: 'var(--t-4)' }}>No enrichment data available.</div>
                      )}
                    </div>
                    <div className="dp-sec">
                      <div className="dp-sec-lbl">Timeline</div>
                      <div className="tl-list">{renderTimeline(selectedAlert.timeline)}</div>
                    </div>
                    <div className="dp-sec">
                      <div className="dp-sec-lbl">Analyst Notes</div>
                      <textarea className="notes-ta" placeholder="Add investigation notes, hypothesis, findings..." />
                      <div className="notes-save"><button type="button" className="notes-save-btn"><i className="ti ti-device-floppy" style={{ fontSize: '11px' }} /> Save Note</button></div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
