import Link from "next/link";

function initials(candidate) {
  const name = candidate.name || candidate.full_name || "Candidate";
  return name
    .split(" ")
    .map((part) => part[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();
}

export default function CandidateCard({ candidate }) {
  const id = candidate.id ?? candidate.candidate_id;
  const name = candidate.name || candidate.full_name || "Unnamed candidate";
  const email = candidate.email || candidate.email_address || "No email provided";
  const role = candidate.role || candidate.position || candidate.job_title;

  return (
    <Link className="candidate-card" href={`/candidates/${id}`}>
      <div className="candidate-card__topline">
        <span className="avatar">{initials(candidate)}</span>
        <span className="candidate-card__arrow" aria-hidden="true">
          ↗
        </span>
      </div>
      <h3>{name}</h3>
      <p className="candidate-card__email">{email}</p>
      {role && <p className="candidate-card__role">{role}</p>}
      <div className="candidate-card__meta">
        {candidate.location && <span>{candidate.location}</span>}
        {candidate.experience && <span>{candidate.experience}</span>}
      </div>
    </Link>
  );
}