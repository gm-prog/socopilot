import { useNotificationStore } from "../store/notificationStore";

export default function NotificationToast() {
  const notifications = useNotificationStore((s) => s.notifications);
  const dismiss = useNotificationStore((s) => s.dismiss);

  if (notifications.length === 0) return null;

  return (
    <div className="fixed bottom-4 right-4 z-[9999] flex flex-col gap-2 max-w-sm w-full pointer-events-none">
      {notifications.slice(0, 3).map((n) => (
        <div
          key={n.id}
          role="alert"
          className={`pointer-events-auto border px-4 py-3 text-xs font-mono shadow-lg backdrop-blur-sm ${
            n.level === "error"
              ? "border-[#ff3333]/60 bg-[#1c0808]/95 text-[#ff3333]"
              : n.level === "warning"
                ? "border-[#ffcc00]/60 bg-[#1c1610]/95 text-[#ffcc00]"
                : "border-[#9e5b00]/40 bg-[#120e0a]/95 text-[#ff9100]"
          }`}
        >
          <div className="flex items-start justify-between gap-3">
            <span className="leading-relaxed">{n.message}</span>
            <button
              type="button"
              onClick={() => dismiss(n.id)}
              className="text-[#9e5b00] hover:text-white shrink-0"
              aria-label="Dismiss"
            >
              ×
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}
