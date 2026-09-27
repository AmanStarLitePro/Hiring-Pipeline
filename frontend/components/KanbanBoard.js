import Link from "next/link";
import { useState } from "react";
import { addCandidate, getCandidates } from "../lib/api";

const DEFAULT_STAGES = [
  "applied",
  "screening",
  "interview",
  "offer",
  "hired",
  "rejected",
];

function stageName(stage) {
  return String(stage || "Unstaged")
    .replace(/[_-]/g, " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

export default function KanbanBoard({ candidates: initialCandidates, onCandidateAdded }) {
  const [candidates, setCandidates] = useState(initialCandidates || {});
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [formData, setFormData] = useState({ name: "", email: "" });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const grouped = DEFAULT_STAGES.reduce((acc, stage) => {
    acc[stage] = [];
    return acc;
  }, {});

  if (Array.isArray(candidates)) {
    candidates.forEach((c) => {
      const stage = String(c.current_stage || c.stage || c.status || "Applied").toLowerCase();
      if (!grouped[stage]) grouped[stage] = [];
      grouped[stage].push(c);
    });
  } else if (typeof candidates === "object" && candidates !== null) {
    Object.entries(candidates).forEach(([stageKey, list]) => {
      const normalizedStage = String(stageKey).toLowerCase();
      if (Array.isArray(list)) {
        if (!grouped[normalizedStage]) grouped[normalizedStage] = [];
        grouped[normalizedStage].push(...list);
      }
    });
  }

  const totalCandidates = Object.values(grouped).reduce((acc, list) => acc + list.length, 0);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleCreateCandidate = async (e) => {
    e.preventDefault();
    if (!formData.name.trim() || !formData.email.trim()) {
      setError("Please fill in both name and email.");
      return;
    }

    setSubmitting(true);
    setError("");

    try {
      await addCandidate({
        name: formData.name.trim(),
        email: formData.email.trim(),
      });

      const updatedCandidates = await getCandidates();
      setCandidates(updatedCandidates);
      if (onCandidateAdded) onCandidateAdded(updatedCandidates);

      setFormData({ name: "", email: "" });
      setIsModalOpen(false);
    } catch (err) {
      setError(err.message || "Failed to create candidate.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="kanban-wrapper">
      <div className="board-toolbar">
        <span>Total Candidates: {totalCandidates}</span>
        <button
          onClick={() => setIsModalOpen(true)}
          className="button button--dark"
        >
          + Add Candidate
        </button>
      </div>

      <div className="kanban-board">
        {DEFAULT_STAGES.map((stage) => {
          const list = grouped[stage] || [];
          return (
            <div key={stage} className="kanban-column">
              <div className="kanban-column__header">
                <h2>{stageName(stage)}</h2>
                <span className="count-badge">{list.length}</span>
              </div>
              <div className="kanban-column__cards">
                {list.length === 0 ? (
                  <p className="empty-column">No candidates here.</p>
                ) : (
                  list.map((c) => (
                    <Link
                      key={c.id ?? c.candidate_id}
                      href={`/candidates/${c.id ?? c.candidate_id}`}
                      className="candidate-card"
                    >
                      <div className="candidate-card__topline">
                        <div className="avatar">
                          {(c.name || "U")
                            .split(" ")
                            .map((n) => n[0])
                            .join("")
                            .slice(0, 2)
                            .toUpperCase()}
                        </div>
                        <span className="candidate-card__arrow">→</span>
                      </div>
                      <p className="candidate-card__role">{c.name}</p>
                      <p className="candidate-card__email">{c.email}</p>
                    </Link>
                  ))
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Modal */}
      {isModalOpen && (
        <div className="modal-overlay">
          <div className="modal-card">
            <div className="modal-header">
              <h2>Add New Candidate</h2>
              <button className="close-btn" onClick={() => setIsModalOpen(false)}>
                ✕
              </button>
            </div>
            {error && <div className="alert">{error}</div>}
            <form onSubmit={handleCreateCandidate}>
              <div className="form-group">
                <label htmlFor="candidate-name">Full Name</label>
                <input
                  id="candidate-name"
                  type="text"
                  name="name"
                  placeholder="e.g. Alice Johnson"
                  value={formData.name}
                  onChange={handleInputChange}
                  required
                />
              </div>
              <div className="form-group">
                <label htmlFor="candidate-email">Email Address</label>
                <input
                  id="candidate-email"
                  type="email"
                  name="email"
                  placeholder="e.g. alice@gmail.com"
                  value={formData.email}
                  onChange={handleInputChange}
                  required
                />
              </div>
              <div className="modal-actions">
                <button
                  type="button"
                  className="button button--secondary"
                  onClick={() => setIsModalOpen(false)}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="button button--dark"
                  disabled={submitting}
                >
                  {submitting ? "Adding..." : "Add Candidate"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}