function formatDate(value) {
  if (!value) return "Date unavailable";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("en", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

function eventTitle(event) {
  return (
    event.action ||
    event.event ||
    event.type ||
    event.activity ||
    "Candidate activity"
  );
}

export default function AuditLog({ logs = [], loading = false }) {
  if (loading) return <p className="muted">Loading activity...</p>;
  if (!logs.length) return <p className="muted">No activity recorded yet.</p>;

  return (
    <ol className="audit-log">
      {logs.map((event, index) => (
        <li className="audit-log__item" key={event.id ?? event.log_id ?? index}>
          <span className="audit-log__dot" aria-hidden="true" />
          <div className="audit-log__content">
            <div className="audit-log__heading">
              <strong>{eventTitle(event)}</strong>
              <time dateTime={event.timestamp || event.created_at}>
                {formatDate(event.timestamp || event.created_at || event.date)}
              </time>
            </div>
            <p>
              {event.description ||
                event.details ||
                event.message ||
                event.note ||
                "No additional details."}
            </p>
            {(event.actor || event.user || event.performed_by) && (
              <span className="audit-log__actor">
                by {event.actor || event.user || event.performed_by}
              </span>
            )}
          </div>
        </li>
      ))}
    </ol>
  );
}