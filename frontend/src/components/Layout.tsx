import { Link, useLocation } from "react-router-dom";
import { useState, useRef, useEffect } from "react";
import type { ReactNode } from "react";
import { useUIStore } from '../store/useUIStore';
import ReactDOM from 'react-dom';

interface LayoutProps {
  children: ReactNode;
}

interface Message {
  id: string;
  sender: 'user' | 'copilot';
  text: string;
  timestamp: Date;
}

const nav = [
  { to: "/", label: "Dashboard", icon: "⌘" },
  { to: "/alerts", label: "Alerts", icon: "⚠" },
  { to: "/search", label: "Search", icon: "🔍" },
  { to: "/status", label: "Status", icon: "⛭" },
  { to: "/ops", label: "Ops", icon: "⚙" },
];

export default function Layout({ children }: LayoutProps) {
  const location = useLocation();
  const copilotOpen = useUIStore((state) => state.copilotOpen);
  const setCopilotOpen = useUIStore((state) => state.setCopilotOpen);

  // Chat conversation state
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      sender: "copilot",
      text: "How can I assist you with this alert?",
      timestamp: new Date()
    }
  ]);
  const [inputValue, setInputValue] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll chat to bottom when new messages stream in
  useEffect(() => {
    if (copilotOpen) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, copilotOpen]);

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim()) return;

    const userMsg: Message = {
      id: crypto.randomUUID(),
      sender: 'user',
      text: inputValue.trim(),
      timestamp: new Date()
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputValue("");

    // Simulate AI response after a short timeout
    setTimeout(() => {
      const assistantMsg: Message = {
        id: crypto.randomUUID(),
        sender: 'copilot',
        text: "Analyzing packet capture telemetry and related store transactions. Standing by...",
        timestamp: new Date()
      };
      setMessages((prev) => [...prev, assistantMsg]);
    }, 1000);
  };

  const Modal = () => copilotOpen ? (
    <div className="fixed inset-0 z-[999999] flex items-center justify-center bg-black/80 backdrop-blur-sm">
      <div className="bg-heritage-surface border border-heritage-gold rounded-lg shadow-2xl w-[95%] max-w-2xl h-[80vh] flex flex-col overflow-hidden">
        
        {/* Header */}
        <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-heritage-ink">
          <div className="flex items-center gap-2">
            <span className="text-heritage-gold animate-pulse">●</span>
            <h2 className="text-lg text-heritage-gold font-bold uppercase tracking-wider">AI Copilot Core</h2>
          </div>
          <button 
            onClick={() => setCopilotOpen(false)} 
            className="text-slate-400 hover:text-white border border-slate-800 px-3 py-1 rounded text-xs transition bg-slate-900/40"
          >
            Close
          </button>
        </div>

        {/* Message Log Window */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-black/20">
          {messages.map((msg) => (
            <div 
              key={msg.id} 
              className={`flex flex-col max-w-[85%] ${msg.sender === 'user' ? 'ml-auto items-end' : 'mr-auto items-start'}`}
            >
              <div 
                className={`p-3 rounded-lg text-sm leading-relaxed ${
                  msg.sender === 'user' 
                    ? 'bg-heritage-gold text-black font-semibold' 
                    : 'bg-slate-900 border border-slate-800 text-slate-100'
                }`}
              >
                {msg.text}
              </div>
              <span className="text-[10px] text-slate-500 mt-1 px-1">
                {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </span>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        {/* Interactive Chat Input Form Bar */}
        <form onSubmit={handleSendMessage} className="p-3 border-t border-slate-800 bg-heritage-ink flex gap-2">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="Ask Copilot to analyze signatures, correlations, or code structures..."
            className="flex-1 bg-black border border-slate-800 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-heritage-gold transition placeholder-slate-600"
          />
          <button 
            type="submit" 
            className="px-4 py-2 bg-heritage-gold hover:bg-yellow-600 text-black font-bold rounded text-sm transition tracking-wide uppercase"
          >
            Send
          </button>
        </form>

      </div>
    </div>
  ) : null;

  return (
    <div className="min-h-screen bg-heritage-bg text-heritage-text">
      {ReactDOM.createPortal(<Modal />, document.body)}

      <div className="grid min-h-screen grid-cols-[80px_1fr]">
        <aside className="bg-heritage-ink border-r border-heritage-goldBorder flex flex-col items-center py-6 gap-8">
          <div className="h-14 w-14 rounded-full border border-heritage-goldBorder bg-heritage-surface/90 flex items-center justify-center text-heritage-gold font-serif text-base tracking-[0.35em]">HI</div>
          <nav className="flex flex-col gap-4">
            {nav.map((item) => {
              const active = location.pathname === item.to;
              return (
                <Link key={item.to} to={item.to} title={item.label} className="relative group">
                  <span className={`text-2xl transition duration-400 ease-premium ${active ? "text-heritage-gold" : "text-heritage-muted group-hover:text-heritage-text"}`}>
                    {item.icon}
                  </span>
                </Link>
              );
            })}
          </nav>
        </aside>
        <main className="flex-1 overflow-auto px-8 py-10">{children}</main>
      </div>
    </div>
  );
}
